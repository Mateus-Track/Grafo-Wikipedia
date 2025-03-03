import networkx as nx
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
from pyvis.network import Network
import random

def obter_titulo_pagina(link_relativo):
    url = f"https://pt.wikipedia.org{link_relativo}"
    pagina = requests.get(url)
    soup = BeautifulSoup(pagina.text, "html.parser")
    
    elemento = soup.find(class_="mw-page-title-main")
    if elemento:
        return elemento.text.strip()
    else:
        return "Titulo Desconhecido"
        

def draw_interactive_graph(G, selecionados):
    net = Network(notebook=True, height="800px", width="100%", directed=True) 
    max_degree = max(dict(G.degree()).values()) if G.number_of_nodes() > 0 else 1

    
    for node in G.nodes():
        in_degree = G.in_degree(node)
        out_degree = G.out_degree(node)
        degree = in_degree + out_degree
        size = 15 + (degree / max_degree) * 200
        physics = False if degree > 80 else True

        color = "red" if node in selecionados else "blue"
        # net.add_node(node, label=str(node), title=f"Grau: {G.degree(node)}", color=color, size=size, physics=physics)
        net.add_node(node, label=str(node), title=f"In: {in_degree} | Out: {out_degree}", color=color, size=size, physics=physics)


    for edge in G.edges():
        node1, node2 = edge
        edge_color = "#666666"  
        
        if node1 in selecionados or node2 in selecionados:
            edge_color = "black"

        net.add_edge(node1, node2, color=edge_color, arrows="to")
    
    net.force_atlas_2based(
        gravity=-15, 
        central_gravity=0.001,  
        spring_length=200,  
        spring_strength=0.005, 
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

    G = nx.DiGraph()
    selecionados = []

    pagina_inicial = requests.get("https://pt.wikipedia.org/wiki/Especial:Aleat%C3%B3ria")
    # pagina_inicial = requests.get("https://pt.wikipedia.org/wiki/França")

    proxima_pagina = pagina_inicial

    iteracao = 1
    while(iteracao < 8):
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
                
                if (tag.name == "h2" or tag.name == "h3" or tag.name == "h4" or tag.name == "h1") and tag.get("id") == "Referências":
                    break 

                if tag.name == "a" and tag.has_attr("href"):
                    if tag.find_parent("table", role="presentation"):
                        continue

                    link = tag["href"]
                    
                if link.startswith("/wiki/") and not link.startswith(("/wiki/Ficheiro:", "/wiki/File:", "/wiki/Ajuda:", "/wiki/Wikip", "/wiki/Predefini%C3%A7%C3%A3o:Info")):
                    titulos.append((tag.get("title", "Sem título"), link))

        # for titulo, link in titulos:
            # print(f"Título: {titulo}, Link: {link}")
        
        for node, link in titulos:
            titulo_real = obter_titulo_pagina(link)
            if titulo_real == "Titulo Desconhecido": 
                continue
            if not G.has_node(titulo_real):
                # print(titulo_real)
                G.add_node(titulo_real)
            G.add_edge(nome, titulo_real)

        print("Finalizado esse node")
        
        if titulos:
            titulo_aleatorio, link_aleatorio = random.choice(titulos)
            proximo = "https://pt.wikipedia.org" + link_aleatorio
            verificacao_proximo = obter_titulo_pagina(link_aleatorio)
            while((titulo_aleatorio in selecionados) or (verificacao_proximo == "Titulo Desconhecido")):
                titulo_aleatorio, link_aleatorio = random.choice(titulos)
                proximo = "https://pt.wikipedia.org" + link_aleatorio
                verificacao_proximo = obter_titulo_pagina(proximo)
        else:
            proximo = None
            break


        proxima_pagina = requests.get(proximo)

        iteracao += 1

    draw_interactive_graph(G, selecionados)