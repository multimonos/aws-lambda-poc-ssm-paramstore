.PHONY: default test

include .env
export 


# config
env?=dev
conf:=conf/$(env).json
fn=$(env)-poc-ssm

# build / prepare vars
src=src
dist=dist
target=dist/target.zip

default: # noop
	@echo "env : $(env)" \
	&& echo "app : $(app)" \
	&& echo "fn  : $(fn)"   \
	&& echo "conf: $(conf)" 
	@cat $(conf)

identity: # configure aws user
	aws sts get-caller-identity

test:
	clear && python -m pytest -vs

test-ssm:
	clear && python -m pytest -vs test_ssm.py

test-lambda:
	clear && python -m pytest -vs test_lambda.py

prepare:
	git rev-parse HEAD > src/commit.txt \
	&& mkdir -p $(dist) \
	&& rm -f $(target) \
	&& (cd $(src) && zip -r ../$(target) . -x ".*" "__pycache__/*" "venv/*") 


validate:
	@test -n "$(env)" || { echo "❌ Missing required variable : env"; exit 1; } 
	@test -n "$(app)" || { echo "❌ Missing required variable : app"; exit 1; }
	@test -f $(conf) || (echo "❌ Config file not found : $(conf)" && exit 1)
	@make default

invoke: validate
	@aws lambda invoke --function-name $(fn) --payload "{}" res.json && cat res.json |jq

prepare: 
	git rev-parse HEAD > src/commit.txt \
	&& mkdir -p $(dist) \
	&& rm -f $(target) \
	&& (cd $(src) && zip -r ../$(target) . -x ".*" "__pycache__/*" "venv/*") 

deploy: validate prepare
	aws lambda update-function-code --function-name $(fn) --zip-file fileb://$(target) --no-cli-pager \
	&& sleep 5 \
	&& ENV_CONFIG=$$(jq -c .Environment $(conf)) \
	&& aws lambda update-function-configuration --function-name $(fn) --environment "$$ENV_CONFIG" --no-cli-pager 
