source ./offline.env
llama-server -hf "${LLAMACPP_MODEL:-$OPENAI_MODEL}" --reasoning off
