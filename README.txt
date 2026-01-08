Tentative ideas:

- Download a copy of the bioshock fandom wiki and feed it to a RAG system.

- Store the resulting embeddings in a database on the cloud
	- One database for articles only (Canon)
	- One database for user-generated content (Non-canon/Theories)

- Using Langchain create an agent that can
	Lore-Agent:
		- converse with users
		- use a tool to query using the RAG system
		- Provide high quality, no fluff answers
	Theory-Agent:
		- converse with users
		- access to the theories database
			- explicitly states the speculative nature of it's replies
	Up-to-date-agent:
		- Access to /r/bioshock and all it's more up to date and current information

- Discord bot as front end for discussing with agent


- Advanced: Multi-step reasoning?  "Who where the first big daddies to be created?"
	