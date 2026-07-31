

## pasos previos

# install uv
sudo snap install astral-uv --classic

# install specify-cli
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

## init proyect/worsksoace
cd /path/to/workspace/proyect

# Initialize specify ( for codex ) 
specify init --here --integration codex

# Initialize bmad ( for codex and claude )
npx bmad-method install

# Import skills

# Creat symliks para claude

# Generar contexto del proyecto: bmad-generate-project-context

# Creat symliks para CLAUDE.md y AGENTS.md -> doc/project-context.md

# Ensure .gitignore rules
.specify
