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

## How to use
TBD

## Packages used
TBD

## FAQs

*Will jinny ever integrate with Kubernetes directly?*
Maybe. The Kubernetes API is fairly organised but the preprovided SDKs are autogenerated nightmares. If there's a way to work around that, which there probably is, then maybe. As an engineer I'm much keener to lean on kubectl as interacting with the Kubernetes API is kubectl's job.

*Can I donate or support?*
Nah. I'm good. If jinny really helps and you want to right the balance then please donate to the Guide Dogs UK or Australia or Tassie. With some time, energy and some delicious dog treats they give people back their independence, it's the best ROI I know of.

https://www.guidedogs.org.uk
https://guidedogs.com.au
https://guidedogstas.com.au/supportus/donate/

*Can you offer support?*
jinny is simple enough that your problem isn't likely to be jinny itself. If it is then open up an issue here on Gitlab or on Github.