<p align="center">
  <img width="317" height="500" src="https://raw.githubusercontent.com/smashthings/jinny/pipeline/logo.png">
</p>

# jinny

Jinny is a templating tool for jinja templates. It can be used for a number of things but was created from a DevOps perspective to aid in configuration management for scaled deployments instead of using tools like Helm, Kustomize, jinja-cli, etc. These days jinny is still used for Ops work but is also used for live applications handling email templating, static HTML generation and more

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

## CLI Usage Examples
```

=> Templating multiple templates with a single input file:
$ jinny -t template-1.txt template-2.txt -i inputs.yml

=> Templating any number of templates with two input files where base-values.yml provides all the base values and any values in overrides.json acts as an override:
$ jinny -t template.yml -i base-values.yml overrides.json

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

## Module Usage Examples

Jinny is primarily a CLI tool, and python packaging can get incredibly painful, however, for simple use cases Jinny still works as a module and has been used in production environments for things like email templating (ie, data from a contact POST request => values for HTML email template to send to internal teams)


```

# Import all helpers and standard elements of Jinny
import jinny.jinny as jinny

# And then use it as in this production example
tmpl = jinny.TemplateHandler(templateName="email", rawString=tmplData)
tmpl.Render({
  'rows': parsedBody
})

print(tmpl.result)


# Values can be exactly defined as the above or you can use the helper functions to give you the same features 
mergedDict = jinny.CombineValues({
  "first": True
}, {
  "second": "please"
}, 'test_merging_dicts')

assert mergedDict["first"] == True
assert mergedDict["second"] == "please"

mergedDict["rows"] = []

jinny.SetNestedValue(mergedDict, ["rows", "0"], "firstItem")

tmpl = jinny.TemplateHandler(templateName="email-two", rawString=tmplData)
tmpl.Render(mergedDict)

print(tmpl.result)


```

## Enhancements
Jinny is opinionated. This means that it does things like trim template whitespace by default so you don't have to debug whitespace in your output. However, it's also opinionated in that the base jinja filters and objects can and have been expanded to provide appropriate functionality that is common jinny's use cases.

**Filters**

*file_content*


```
$ cat template.html

<html>
<style>
{{ ( path.templatedir + "css.css" ) | file_content }}
</style>
</html>

$ cat css.css

html { font-weight: 900; }

$ jinny -t template.html
<html>
<style>
html { font-weight: 900; }
</style>
</html>


```

**Globals**

*path*


path is a global dict that is available on each template. It'll give you the variables for:

- cwd - the current working directory
- jinny - jinny's directory, ie the jinny module itself
- template - the full path of the template currently being templated
- templatedir - the directory of the template currently being templated
- home - the home directory

These are global values so you can access them whenever and easily combined them into paths that work locally or in unstable environments such as inside pipelines

```
$ cat template.txt
I'm working from {{ path.cwd }}
jinny is running from {{ path.jinny }}
This template is {{ path.template }} in the directory {{ path.templatedir }}
My home directory with all my cat pics and DRG screenshots is {{ path.home }}

Rock and Stone!

$ jinny -t template.txt
I'm working from /home/smashthings/jinny-tmp/
jinny is running from /home/smashthings/.local/bin/jinny
This template is /home/smashthings/jinny-tmp/template.txt in the directory /home/smashthings/jinny-tmp/
My home directory with all my cat pics and DRG screenshots is /home/smashthings/

Rock and Stone!


```

*time_now*

time_now will generate a timestamp at the UTC time that it's called and return the timestamp based on the provided format string based on datetime's strftime. If you don't provide a format it'll return the microsecond ISO timestamp

https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior


```
$ cat template.txt
#### => Template Start: {{ time_now("%M:%S.%f") }}

The exact UTC time down to the microsecond is {{ time_now() }}
But if you just wanted to know what time it is for humans it's {{ time_now("%Y-%m-%dT%H:%M") }}
Or you could say {{ time_now("%A the %j day of %Y which is also the %d day of %B") }}

#### => Template Finish: {{ time_now("%M:%S.%f") }}

$ jinny -t template.txt
#### => Template Start: 28:42.871426

The exact UTC time down to the microsecond is 2022-12-31T08:28:42.871447
But if you just wanted to know what time it is for humans it's 2022-12-31T08:28
Or you could say Saturday the 365 day of 2022 which is also the 31 day of December

#### => Template Finish: 28:42.871465


```

## Packages used
Check out src/jinny/requirements.txt

As of December 2022 only PyYAML and Jinja2 are used outside the base library

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

