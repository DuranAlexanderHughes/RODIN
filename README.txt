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


api.py

- Start the fastapi server via `uvicorn backend.app.api:app --reload` in a seperate CMD terminal
- navigate to http://127.0.0.1:8000/docs and use the POST /ask Swagger UI dropdown to post a question
	- alternatively	a terminal command such as `curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"local","message":"Who is Andrew Ryan?"}'
` can be used for a similar result.