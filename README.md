> :warning: **jinny is now in beta, it should work but don't bet a kidney on it**


<p align="center">
  <img width="317" height="500" src="https://raw.githubusercontent.com/smashthings/jinny/pipeline/logo.png">
</p>

# jinny

Jinny is a templating tool for jinja templates. It can be used for a number of things but was created from a DevOps perspective to aid in configuration management for scaled deployments instead of using tools like Helm, Kustomize, jinja-cli, etc.

## Use Cases & Why

The 2020's of software usually include mashing together different/underlying/proxied systems that need to be able to scale, adapt and transform in unstable environments (no pets, black box providers, etc) and unstable direction. This means you're running applications and controlling services that lead to a mass of config that needs to change on a whim. Add to this the need to pass this through various CI/CD pipelines and there's a need for a templating application that is:

- Command line controlled
- Can take multiple JSON & YAML template inputs
- Can take multiple Jinja based templates
- Can choose to template out to stdout, to separate files, to one big file
- Allows for cascading overwriting of inputs
- Alows the utilising of a seasoned templating language with some room for adding functionality
- Stable - uses simple and reliable libraries and doesn't need constant maintenance. We don't want this failing our pipelines or botching deployments

For example, Jinny was originally conceived as a way to handle templating of Kubernetes manifests rather than using Helm or other Go templating tools. Helm is overengineered for what I often need and usually comes with unwanted issues such as nuking production environments (your milage may vary). Jinny doesn't attempt Kubernetes package management, whatever that is, and instead just sticks to templating such that you as the Ops engineer can choose how, when or what to apply.

## Usage Examples
```

=> Templating multiple templates with a single input file:
$ jinny -t template-1.txt template-2.txt -i inputs.yml

=> Templating any number of templates with two input files where base-values.yml provides all the base values and any values in overrides.json acts as an override:
$ jinny -t template.yml -i base-values.yml overrides.json

=> Add even more overrides via environment variables, so your pipelines can completely replace any bad value:
$ JINNY_overridden_value="top-priority" jinny -t template.yml -i base-values.yml overrides.json

=> Pump all your files to a single stdout stream with a separator so different files are clearly marked:
$ jinny -t template-1.yml template-2.yml -i inputs.json -s '---'

=> Dump all your templated files into a directory for capture
$ jinny -t template-1.yml template-2.yml -i inputes.json -d /path/to/directory
$ kubectl diff -f /path/to/directory
$ kubectl apply --server-dry-run -f /path/to/directory

=> Pipe jinny to kubectl for appropriate templating without having to result to Helm
$ jinny -t template-1.yml -i inputs.json | kubectl apply -f -

```

## Packages used
Check out src/jinny/requirements.txt

As of May 2022 only PyYAML and Jinja2 are used

## FAQs

*Will jinny ever integrate with Kubernetes directly?*
Maybe. The Kubernetes API is fairly organised but the preprovided SDKs are autogenerated nightmares. If there's a way to work around that, which there probably is, then maybe. As an engineer I'm much keener to lean on kubectl as interacting with the Kubernetes API is kubectl's job.

*What about Windows?*
My Windows days are behind me and I'm not coming back to it. If you'll like to PR it in go for it, however I'm neither motivated nor tooled up to maintain support for Windows.

*Can I donate or support?*
Nah. I'm good. If jinny really helps and you want to right the balance then please donate to the Guide Dogs UK or Australia or Tassie. With some time, energy and some delicious dog treats they give people back their independence, it's the best ROI I know of.

https://www.guidedogs.org.uk \
https://guidedogs.com.au \
https://guidedogstas.com.au/supportus/donate/

*Can you offer support?*
jinny is simple enough that your problem isn't likely to be jinny itself. If it is then open up an issue here on Gitlab or on Github.