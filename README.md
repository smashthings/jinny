<p align="center">
  <img width="317" height="500" src="https://github.com/smashthings/jinny/blob/master/docs/img/logo.png?raw=true">
</p>

# jinny

jinny is a CLI tool that renders Jinja templates using layered values files, environment variables and CLI overrides - designed for DevOps pipelines and configuration generation without the overhead of Helm or custom Python glue scripts.

Modern infrastructure often requires generating large volumes of configuration (Kubernetes manifests, service configs, environment bundles, static assets). Existing approaches typically force you to:

- Write and maintain custom Python templating scripts
- Use heavy packaging/deployment tools when you only need templating
- Accept limited or awkward templating systems

jinny focuses on doing one job well: take templates + take values + render deterministic output, with predictable override precedence and CI-friendly behavior.

## Key Capabilities

- Render one or many templates in a single command
- Merge multiple YAML/JSON/env input files with deterministic override order
- Apply environment variable and CLI overrides for pipeline control
- Output to stdout, a single file, or to structured directories for deployment tooling
- Extend Jinja with practical filters and globals for real-world infrastructure templating

jinny was originally built to template Kubernetes manifests without relying on Helm-style Go templating, but it is equally suited for any configuration or text-generation workflow including generating static site HTML, HTML email generation, templating nested configuration files, and more.

## Replace Helm templating with jinny in 30 seconds

If you only need templating (not Helm packaging, charts, or release management), jinny provides a simpler workflow.

**1. Create your template**

```yaml
# deployment.yaml.j2
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ app.name }}
spec:
  replicas: {{ app.replicas }}
```

**2. Define environment values**

```yaml
# values-prod.yaml
app:
  name: example-service
  replicas: 3
```

**3. Render and apply**

```bash
jinny -t deployment.yaml.j2 -i values-prod.yaml | kubectl apply -f -
```

That’s it — no charts, no Go templates, no packaging layers.

jinny focuses purely on **deterministic template rendering with layered values**, making it ideal when you want Helm-style templating flexibility without Helm’s operational overhead.

Common reasons teams switch:

* **Use Jinja instead of Go templates**
  Jinja provides clearer syntax, better control structures, and easier maintainability for complex templates.

* **Remove chart and release overhead**
  When you only need template rendering, Helm’s chart structure, packaging, and release tracking add operational complexity without providing value.

* **Deterministic layered values handling**
  jinny merges multiple values files, environment variables, and CLI overrides with predictable precedence, making environment-specific rendering straightforward.

* **Simpler CI/CD integration**
  jinny outputs directly to stdout or structured directories, allowing seamless integration with tools such as `kubectl`, configuration deployment pipelines, and build systems.

* **Delete custom templating scripts**
  Instead of maintaining internal Python templating utilities, teams can standardize on a dedicated CLI renderer designed for infrastructure workflows.

jinny is best suited for environments where **configuration rendering is required**, but **application packaging and release management are handled elsewhere**.


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

jinny is far more than just jinja templating with the user manual available at - [https://jinny.southall.solutions](https://jinny.southall.solutions).

This manual itself serves as an example of jinny templating. The entire page is a single static HTML page templated with jinny using nested templates and layered configuration. The source code for the site is at `docs/*` and contains:

- The main `index.html` page
- `docs/inputs/*` - containing `yml` files that cover separate content and configuration
- `docs/partials/*` - covering separate HTML parials which jinny collates into the single page
- `docs/css/*` && `docs/js/*` - static files that jinny dynamically loads in a build time with the templating provided at `index.html`
- `docs/img/*` - static images that jinny reads, base64 encodes and integrates directly into the HTML
- All the other frontend stuff

The directory tree is as standard as you can expect, but with jinny's features the whole functionality is compiled and deployed into a single HTML page.

