<p align="center">
  <img width="317" height="500" src="https://github.com/smashthings/jinny/blob/master/docs/img/logo.png?raw=true">
</p>

# jinny

Jinny is a templating tool for jinja templates. It can be used for a number of things but was created from a DevOps perspective to aid in configuration management for scaled deployments instead of using tools like Helm, Kustomize, jinja-cli, etc. These days jinny is still used for Ops work but is also used for live applications handling email templating, static HTML generation and more


## CLI Usage Examples

```

=> Templating multiple templates with a single input file:
$ jinny -t template-1.txt template-2.txt -i inputs.yml

=> Templating any number of templates with two input files where base-values.yml provides all the base values and any values in overrides.json acts as an override:
$ jinny -t template.yml -i base-values.yml overrides.json

=> Use an environment value file for templating
$ jinny -t template.yml -i ENVIRONMENT_VARIABLES.env

=> Add an explicit override via CLI argument -e
$ jinny -t template.yml -i base-values.yml -e 'image=smasherofallthings/flask-waitress:latest'

=> Add even more overrides via environment variables, so your pipelines can completely replace any bad value:
$ JINNY_overridden_value="top-priority" jinny -t template.yml -i base-values.yml overrides.json

=> Pump all your files to a single stdout stream with a separator so different files are clearly marked:
$ jinny -t template-1.yml template-2.yml -i inputs.json -s '---'

=> Dump all your templated files into a directory for capture, comparison and deployment
$ jinny -t template-1.yml template-2.yml -i inputs.json -d /path/to/directory
$ kubectl diff -f /path/to/directory
$ kubectl apply --server-dry-run -f /path/to/directory

=> Pipe jinny to kubectl directly
$ jinny -t template-1.yml -i inputs.json | kubectl apply -f -

```

## Documentation

Jinny has a lot of functionality, settings and more. You can review the documentation at - [https://jinny.southall.solutions](https://jinny.southall.solutions).

The documentation is a single HTML page built with Jinny. The source code for the site is at `docs/*` and contains:

- The main `index.html` page
- `docs/inputs/*` - containing `yml` files that cover separate content and configuration
- `docs/partials/*` - covering separate HTML parials which jinny collates into the single page
- `docs/css/*` && `docs/js/*` - static files that jinny dynamically loads in a build time with the templating provided at `index.html`
- `docs/img/*` - static images that jinny reads, base64 encodes and integrates directly into the HTML
- All the other frontend stuff

The directory tree is as standard as you can expect, but with jinny's features the whole functionality is compiled and deployed into a single HTML page.

