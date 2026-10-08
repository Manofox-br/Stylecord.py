# Começando...
> Aprenda a iniciar o client e fazer coisas básicas.

---

1. Vamos começar importando as blibiotecas nessesarias:
```py
import stylecord
```

2. **Definir os __[itents](models#intents.md)__ nescessário para o client:**
```py
intents = stylecord.Intents()
```


3. **Criar uma variável para representar o client:**
```py
client = stylecord.Client(intents=intents)
```

4. **Função __[on_ready](events#on_ready.md)__ para o capturar o início do bot:**
```py
@client.event # decorador que diz ao python: Ei! essa função é um evento que teve ser chamado.
async def on_ready():
    print(f"O client {client.user.tag} acabou de logar!")
```

5. **Finalmente, chegou a hora de iniciar o client:**
```py
client.run("SEU-TOKEN")
```
#### *Troque 'SEU-TOKEN' pelo token da sua aplicação do [Discord Devloper Portal](https://www.discord.com/developers/applications)

### 📜 CÓDIGO COMPLETO:
```py
import stylecord

intents = stylecord.Intents()

client = stylecord.Client(intents=intents)

@client.event # decorador que diz ao python: Ei! essa função é um evento que teve ser chamado.
async def on_ready():
    print(f"O client {client.user.tag} acabou de logar!")

client.run("SEU-TOKEN")
```