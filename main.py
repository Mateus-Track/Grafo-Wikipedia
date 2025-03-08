import parametros
import networkx as nx
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
from pyvis.network import Network
import random
import json


def obter_titulo_pagina(link_relativo):
    url = f"https://pt.wikipedia.org{link_relativo}"
    pagina = requests.get(url, allow_redirects=True)
    soup = BeautifulSoup(pagina.text, "html.parser")
    
    elemento = soup.find(class_="mw-page-title-main")
    if elemento:
        return elemento.text.strip()
    else:
        titulo_italico = soup.find(class_="firstHeading mw-first-heading")
        if(titulo_italico):
            return titulo_italico.text.strip()
        return "Titulo Desconhecido"



def salvar_grafo(G, selecionados, filename=parametros.ARQUIVO_SAIDA_GRAFO):
    for node in G.nodes():
        G.nodes[node]['selecionado'] = node in selecionados 

    data = nx.node_link_data(G)  
    with open(filename, "w") as f:
        json.dump(data, f)  

def carregar_grafo(filename=parametros.ARQUIVO_ENTRADA_GRAFO):
    with open(filename, "r") as f:
        data = json.load(f)  

    G = nx.node_link_graph(data) 
    
    selecionados = [node for node, attrs in G.nodes(data=True) if attrs.get("selecionado", False)]

    return G, selecionados


def draw_interactive_graph(G, selecionados):
    net = Network(notebook=True, height="800px", width="100%", directed=True) 
    max_degree = max(dict(G.degree()).values()) if G.number_of_nodes() > 0 else 1

    
    for node in G.nodes():
        in_degree = G.in_degree(node)
        out_degree = G.out_degree(node)
        degree = in_degree + out_degree
        size = 15 + (degree / max_degree) * 220
        physics = False if degree > 80 else True

        color = "red" if node in selecionados else "blue"
        # net.add_node(node, label=str(node), title=f"Grau: {G.degree(node)}", color=color, size=size, physics=physics)
        net.add_node(node, label=str(node), title=f"In: {in_degree} | Out: {out_degree}", color=color, size=size, physics=physics)


    for edge in G.edges():
        node1, node2 = edge
        edge_color = "#666666"  
        
        if node1 in selecionados or node2 in selecionados:
            edge_color = "#999999"

        net.add_edge(node1, node2, color=edge_color, arrows="to")
    
    net.force_atlas_2based(
        gravity=-15, 
        central_gravity=0.001,  
        spring_length=200,  
        spring_strength=0.009, 
        damping=0.95  
    )

    # net.set_options("""
    # var options = {
    #   "physics": {
    #     "stabilization": {
    #       "enabled": true,
    #       "iterations": 200,
    #       "fit": true
    #     }
    #   }
    # }
    # """)

    net.show("graph.html")

if __name__ == "__main__": 

    escolha_grafo = int(input("Deseja iniciar um novo grafo (1), ou partir do grafo já armazenado (2): "))
    while escolha_grafo != 1 and escolha_grafo != 2:
        escolha_grafo = int(input("Escolha un dos dois! Deseja iniciar um novo grafo (1), ou partir do grafo já armazenado (2): "))
    if escolha_grafo == 1:
        G = nx.DiGraph()
        selecionados = []
        pagina_inicial = requests.get(parametros.PAGINA_INICIAL)
    elif escolha_grafo == 2:
        G,selecionados = carregar_grafo()
        novo_selecionado = random.choice(list(G.nodes))
        while(novo_selecionado in selecionados):
            novo_selecionado = random.choice(list(G.nodes))
        novo_link = "https://pt.wikipedia.org/wiki/" + novo_selecionado.replace(" ", "_")
        pagina_inicial = requests.get(novo_link)
        selecionados.append(novo_selecionado)
    # pagina_inicial = requests.get("https://pt.wikipedia.org/wiki/Ilha_de_São_Jorge")

    proxima_pagina = pagina_inicial

    iteracao = 0
    while(iteracao < parametros.NUMERO_ITERACOES):
        soup = BeautifulSoup(proxima_pagina.text, "html.parser")
        nome = soup.find(class_="mw-page-title-main").text
        if(iteracao == 1):
            G.add_node(nome)
        print("Pagina atual = " + nome)
        selecionados.append(nome)

        conteudo_div = soup.find("div", class_="mw-content-ltr mw-parser-output")
        titulos = []
        if conteudo_div:
            
            for tag in conteudo_div.find_all(["h2", "h3", "h4", "a"]): 
                
                if (tag.name == "h2" or tag.name == "h3" or tag.name == "h4" or tag.name == "h1") and (tag.get("id") == "Referências" or tag.get("id") == "Notas" or tag.get("id") == "Bibliografia" or tag.get("id") == "Ver_também" or tag.get("id") == "Ligações_externas"):
                    break 

                if tag.name == "a" and tag.has_attr("href"):
                    if tag.find_parent("table", role="presentation"):
                        continue

                    link = tag["href"]
                    
                if link.startswith("/wiki/") and not link.startswith(("/wiki/Ficheiro:", "/wiki/File:", "/wiki/Ajuda:", "/wiki/Wikip", "/wiki/Predefini%C3%A7%C3%A3o:Info", "/wiki/Portal:")):
                    titulos.append((tag.get("title", "Sem título"), link))

        # for titulo, link in titulos:
            # print(f"Título: {titulo}, Link: {link}")
        
        for node, link in titulos:
            titulo_real = obter_titulo_pagina(link)
            if titulo_real == "Titulo Desconhecido":
                print("NÃO Aceitou - " + link, titulo_real)
                continue
            print("Aceitou - " + link, titulo_real)
            if not G.has_node(titulo_real):
                # print(link , titulo_real)
                if(titulo_real == "Baleação"):
                    link_baleia = link
                G.add_node(titulo_real)
            G.add_edge(nome, titulo_real)

        print("Finalizado esse node")
        
        if titulos:
            _, link_aleatorio = random.choice(titulos)
            proximo = "https://pt.wikipedia.org" + link_aleatorio
            print("Indo verificar o link: " + link_aleatorio)
            verificacao_proximo = obter_titulo_pagina(link_aleatorio)
            while((verificacao_proximo in selecionados) or (verificacao_proximo == "Titulo Desconhecido")):
                _, link_aleatorio = random.choice(titulos)
                proximo = "https://pt.wikipedia.org" + link_aleatorio
                # print("Indo verificar o link: " + proximo)

                verificacao_proximo = obter_titulo_pagina(link_aleatorio)
        else:
            proximo = None
            break
        
        print("Proximo escolhido = " + proximo)

        proxima_pagina = requests.get(proximo)

        iteracao += 1

    salvar_grafo(G, selecionados)

    draw_interactive_graph(G, selecionados)