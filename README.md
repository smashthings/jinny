<p align="center">
  <img width="317" height="500" src="https://raw.githubusercontent.com/smashthings/jinny/pipeline/logo.png">
</p>

# jinny

Jinny is a templating tool for jinja templates. It can be used for a number of things but was created from a DevOps perspective to aid in configuration management for scaled deployments instead of using tools like Helm, Kustomize, jinja-cli, etc. These days jinny is still used for Ops work but is also used for live applications handling email templating, static HTML generation and more

## Use Cases

Some example use cases will be provided in `examples/*`, at a high level jinny has been used for:

- A lightweight templating tool for Kubernetes manifests
- Templating environment variable files for use with docker images
- Email & HTTP templating within AWS Lambda functions
- Local development templating for static frontends


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

Jinny is opinionated. This means that it makes choices and provides functionality outside of the standard Jinja toolset. One opinion includes automatically trimming template whitespace leaving outputs easier to read. Additionally, the below filters and global functions have been added to improve jinny's usefulness out in the wild.

### Filters

#### file_content

Fully imports the raw content of a file into the template where called:

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

#### nested_template

Imports and templates other templates with the same values as the master template has received. This may not be thread safe for non-GIL or other multithreaded implementations of python as it relies on pointer updates to a global variable from the root template. For CPython which is the vast majority of implementations and runtime this is totally fine.

The benefit of this approach is dodging passing the value stack through the Jinja codebase which can be prone to breaking in Jinja updates and adds a substantial overhead to route and debug. This functionality is well outside of the Jinja's intended design. If you don't want to deviate too far from Jinja then don't use it.

```
$ cat template.html

<html>
<style>
{{ ( path.templatedir + "css.css" ) | nested_template }}
</style>
</html>

$ cat css.css

html { font-weight: {{ font_weight }}; }

$ jinny -t template.html -e font_weight=600
<html>
<style>
html { font-weight: 600; }
</style>
</html>


```

#### print_stdout, print_stderr & tee

These filters will print to stdout, stderr or tee to stdout and continue to content. They're used for debugging, warnings and other elements.

You are going to want to run this with -d or -di options so that resulting templates are written to files rather than dumped to standard out. Not doing that will mix the output of these filters into your template output. 

With that caveat in mind this allows for template annotations within the templating process telling you what's going on without having to analyse the output:

```
$ cat template.html

<html>
<style>
  {{ ("Running a build of this template " + path.template + " at: ") | print_stdout }}
  <h1> This page was generated at {{ time_now() | tee }}</h1>
</style>
</html>


$ jinny -t template.html --dump-to-dir "$(pwd)"
Running a build of this template /home/smashthings/jinny-tmp/template.html at: 
2023-01-23T19:42:56.581482

$ cat 0-template.html
<html>
<style>
  
  <h1> This page was generated at 2023-01-23T19:42:56.581482</h1>
</style>
</html>


```

#### basename, dirname

Straight python rips of os.path.basename and os.path.dirname

```
$ cat template.txt

home: {{ path.home }}
dirname: {{ path.home | dirname }}
basename: {{ (path.home + '.ssh') | basename }}

$ jinny -t template.txt
home: /home/smashthings/
dirname: /home/smashthings
basename: .ssh

```

#### removesuffix, removeprefix

These are rips of the str methods available in Python 3.9 onwards. However, you might be running a version earlier than 3.9, hence these functions are stand alone and can be used in any Python 3 version.

```
$ cat template.txt

removeprefix: {{ "mushroomfactory" | removeprefix("mushroom") }}
dontremoveprefix: {{ "mushroomfactory" | removeprefix("badger") }}

removesuffix: {{ "mushroomfactory" | removesuffix("ory") }}
dontremovesuffix: {{ "mushroomfactory" | removesuffix("badger") }}

$ jinny -t template.txt

removeprefix: factory
dontremoveprefix: mushroomfactory

removesuffix: mushroomfact
dontremovesuffix: mushroomfactory


```

#### censor

Censors the provided string with the ability to set the censor characters, skip censoring the first and/or last *n* characters or always set the censored string to *x* characters long.

```
$ cat template.txt
---
censored_password: {{ req_envvar('PASSWORD') | censor }}
censored_password_always_10_characters: {{ req_envvar('PASSWORD') | censor(fixed_length=10) }}
censored_password_with_birds: "{{ req_envvar('PASSWORD') | censor(vals=['🐦‍']) }}"
censored_password_except_first_2_characters: {{ req_envvar('PASSWORD') | censor(except_beginning=2) }}
censor_everything_except_first_and_last_characters: {{ req_envvar('PASSWORD') | censor(except_beginning=1,except_end=1) }}
passwords_are_always_five_frogs: "{{ req_envvar('PASSWORD') | censor(vals=['🐸'], fixed_length=5) }}"


$ PASSWORD=mushrooms jinny -t template.txt
---
censored_password: *********
censored_password_always_10_characters: **********
censored_password_with_birds: "🐦‍🐦‍🐦‍🐦‍🐦‍🐦‍🐦‍🐦‍🐦‍"
censored_password_except_first_2_characters: mu*******
censor_everything_except_first_and_last_characters: m*******s
passwords_are_always_five_frogs: "🐸🐸🐸🐸🐸"


```


### Globals

#### path

path is a global dict that is available on each template. It'll give you the variables for:

- cwd - the current working directory
- jinny - jinny's directory, ie the jinny module itself
- template - the full path of the template currently being templated
- templatedir - the directory of the template currently being templated
- home - the home directory

These are global values so you can access them whenever and easily combine them into paths that work locally or in unstable environments such as pipelines

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

#### time_now

time_now will generate a UTC timestamp at the point that the function is called. It will provide a microsecond ISO timestamp but with arguments you can provide a strftime compatible string to get the exact output that you're after.

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

#### prompt_envvar

prompt_envvar will prompt you for environment variables that are missing as jinny reaches them in your template(s). Once you provide a value it will set that as an environment variable and continue on, meaning that all other calls for that environment variable will recieve the same value.

This is useful for one off values that don't need to be committed to code or for values that you want to ask for at run time such as passwords.

```
$ cat template.txt
---
I'm driving {{ prompt_envvar('destination') }} for {{ prompt_envvar('event')}}
Oh, I can't wait to see those faces
I'm driving {{ prompt_envvar('destination') }} for {{ prompt_envvar('event')}}, yeah
Well I'm moving down that line
And it's been so long
But I will be there
I sing this song
To pass the time away
Driving in my car
Driving {{ prompt_envvar('destination') }} for {{ prompt_envvar('event')}}%   

$ jinny -t template.txt
Please set variable 'destination':
home
Please set variable 'event':
Christmas
---
I'm driving home for Christmas
Oh, I can't wait to see those faces
I'm driving home for Christmas, yeah
Well I'm moving down that line
And it's been so long
But I will be there
I sing this song
To pass the time away
Driving in my car
Driving home for Christmas

$ destination='to the bottlo' event='a big bag of cans' jinny -t template.txt
---
I'm driving to the bottlo for a big bag of cans
Oh, I can't wait to see those faces
I'm driving to the bottlo for a big bag of cans, yeah
Well I'm moving down that line
And it's been so long
But I will be there
I sing this song
To pass the time away
Driving in my car
Driving to the bottlo for a big bag of cans


```

#### req_envvar

Checks for a required environment variable without prompting. Can take a custom message format and parameters for the printed error message if the environment variable is missing. This follows the same message format as string.format:

https://docs.python.org/3/library/string.html#string.Formatter.format

```
$ cat template.txt
---
super_secret: {{ req_envvar(var='PASSWORD', message_format="Need the password under var {0} yo", message_format_params=['PASSWORD']) }}

$ jinny -t template.txt
*********************
<2023-08-31T19:59:35> - TemplateHandler.Render(): Failed to render template at 'template.txt' with an exception from Jinja, details:
Type:<class 'Exception'>
Value:jinny.global_extensions.req_envvar(): Need the password under var PASSWORD yo
Trace:
...


$ PASSWORD=wizards jinny -t template.txt
---
super_secret: wizards


```

#### get_envvar

Gets an environment variable from the environment and provides a default value if not found. If a default value is not provided get_envvar will return an empty string. Returning an empty string allows for template logic to react to missing environment variables

```
$ cat template.txt
---
missing_env_var: {{ get_envvar(var='BADGERS', default='NO BADGERS') }}
existing_env_var: {{ get_envvar('HOME') }}

{% if get_envvar('BADGERS') | length %}
We got {{ get_envvar('BADGERS') }} badgers from the environment variable BADGERS
{% else %}
The environment variable BADGERS didn't exist so we assume no badgers
{% endif %}

$ jinny -t template.txt
---
missing_env_var: NO BADGERS
existing_env_var: /home/smasherofallthings

The environment variable BADGERS didn't exist so we assume no badgers


$ BADGERS=40 jinny -t template.txt
---
missing_env_var: 40
existing_env_var: /home/smasherofallthings

We got 40 badgers from the environment variable BADGERS


```


#### list_files

list_files will take a directory path and will either recursively or not provide a list of all the files in that path.

This is intended to be used with the **for** keyword for looping through files. Original usecase was for implementing files as keys in a kubernetes configmap.

Note that the below example also makes use of *path*, *file_content* and *basename*, all of which are jinny additions and not in jinja.

```
$ cat configmap.yml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: loadsofscripts
data:
{% for f in list_files(path.templatedir + '/scripts') %}
  {{ f | basename }}: |
{{ f | file_content | indent(4, first=True) }}
{% endfor %}


$ cat scripts/script1.sh
#!/bin/bash
echo "This is script one"

$ cat scripts/script2.sh
#!/bin/bash
echo "This is script 2!"

$ jinny -t configmap.yml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: loadsofscripts
data:
  script1.sh: |
    #!/bin/bash
    echo "This is script one"


  script2.sh: |
    #!/bin/bash
    echo "This is script 2!"



```


#### gen_uuid4

Generates a new version 4 UUID via the python uuid library. There's absolutely no memory on this so don't expect idempotency in your resulting templates, ie every time you run the template you'll get different UUIDs. 

This is *awesome* for generating a load of dummy data

```
$ cat template.txt
{% for f in range(5) %}
{{ gen_uuid4() }}
{% endfor %}

$ jinny -t template.txt
b251f634-a912-4868-bd03-e2ccc3ae7356
4e136ef8-b106-42c9-b98c-9d61a833c523
08f9a05a-01a3-4731-a591-3e07d9876c36
7cc40da8-de29-4e37-80b9-fa3ca60ac0f0
0e044ca0-36b8-4835-ac7c-c7fa5215fdcf


```

## Packages used

Check out src/jinny/requirements.txt

As of December 2022 only PyYAML and Jinja2 are used outside the standard library

## FAQs

*Will jinny ever integrate with Kubernetes directly?*  
No. See below for an example of a workable approach.

*What about Windows?*  
My Windows days are behind me and I'm not coming back to it. If you'll like to PR it in go for it, however I'm neither motivated nor tooled up to maintain support for Windows.

*Can I donate or support?*  
Nah. I'm good. If jinny really helps and you want to right the balance then please donate to the Guide Dogs UK or Australia or Tassie. With some time, energy and some delicious dog treats they give people back their independence, it's the best ROI I know of.

https://www.guidedogs.org.uk \
https://guidedogs.com.au \
https://guidedogstas.com.au/supportus/donate/

*Can you offer support?*  
jinny is simple enough that your problem isn't likely to be jinny itself. If it is then open up an issue here on Gitlab or on Github.

## Why

The 2020's of software usually include mashing together different/underlying/proxied systems that need to be able to scale, adapt and transform in unstable environments (no pets, black box providers, etc) and unstable direction. This means you're running applications and controlling services that lead to a mass of config that needs to change on a whim. Add to this the need to pass this through various CI/CD pipelines and there's a need for a templating application that is:

- Command line controlled
- Can take multiple JSON & YAML template inputs
- Can take multiple Jinja based templates
- Can choose to template out to stdout, to separate files, to one big file
- Allows for cascading overwriting of inputs
- Alows the utilising of a seasoned templating language with some room for adding functionality
- Stable - uses simple and reliable libraries and doesn't need constant maintenance. We don't want this failing our pipelines or botching deployments

For example, Jinny was originally conceived as a way to handle templating of Kubernetes manifests rather than using Helm or other Go templating tools. Helm is overengineered for what I often need and usually comes with unwanted issues such as nuking production environments (your milage may vary). Jinny doesn't attempt Kubernetes package management, whatever that is, and instead just sticks to templating such that you as the Ops engineer can choose how, when or what to apply.

## Kubernetes
With the move to Kubernetes the amount of templating and general boilerplate become quite heavy going. There's less coding of systems and more grabbing what's on the OSS shelf and slamming config into it until it does what you need it to do. I understand the reasoning for it, but a major side effect is that what there's less 'writing code' and more 'managing config'.

In Kubernetes land the dominant technology is Helm. Helm and Jinny both do templating. Helm will also attempt deployment management, but I've also found it used just for the templating.

A large motivator behind Jinny was the contempt I have for Helm. Out of the templating tools that I have used, Jinja is the only one I liked coming back to.† Helm templates feel like a significant downgrade. I also hate Helm atrocious deployment management, however, I couldn't rip Helm out of an environment without at least replacing the templating function. Jinny is there to fill that gap.

Jinny doesn't interface directly with Kubernetes. It probably never will as that risks both insourcing the Kubernetes APIs and expanding the packaging footprint for Jinny, which is a Python application. [I also can't state how much I do not want to deal with this](https://raw.githubusercontent.com/kubernetes-client/python/055fa706b8677207091251998dca80cab5d5afb0/kubernetes/client/api/core_v1_api.py).

If I rationalise what interaction I want between Jinny and K8s, it's essentially:

    jinny template * | kubectl <apply|delete> -f -

So I add that functionality into a couple of shell functions:

*jk* | *kubectl apply*
jk is the name I gave the function but you can use whatever you want. Add this to your shell's run command script at `${HOME}/.bashrc` or similar:

```

function jk(){
  tmp=$(tempfile)
  jinny --stdout-seperator='---' -t "${@}" > $tmp
  if [[ $? == "0" ]]; then
    kubectl apply -f $tmp
  else
    cat $tmp
  fi
  rm -rf $tmp
}

```

The stdout-separator argument places yml separators on each file that you pass through, meaning that you can do cool things like mash in various files and have them all apply at once. The caveats with this approach being:

- There's no input files
- Relies on tempfile and kubectl being installed
- Writes a file to disk or wherever volume tempfile is configured to write to
- It's compatible with my bash/zsh setup but you need to check your own

I'm cool with all of that so works well for me.

*jd* | *kubectl delete*
Is basically the same function but calls 

```
function jd(){
  tmp=$(tempfile)
  jinny --stdout-seperator='---' -t "${@}" > $tmp
  if [[ $? == "0" ]]; then
    kubectl delete -f $tmp
  else
    cat $tmp
  fi
  rm -rf $tmp
}
```

### Other Considered Templating Tools

*Go Templating* \
The context loss on loops drives me mad and makes nested loops near unusable. Sure there's work arounds but a workaround you have to use every time is not something I want in my life.

*Mustache* \
Great until you need logic. I often hit this limitation.

*Handlebars* \
Great, although I do remember hitting some ugly limitations with it that I can't quite remember. Also it's js native and I find ops work to be procedural and therefore an async native runtime to be cumbersome.

*Pug* \
It's HTML specific and I need something that works with *everything*. I'm on the frontlines man, sometimes I'm in the tank, sometimes I'm on the missle turret, I need a single unified interface.

*Jinja* \
Extensible. Simple syntax. Written in my most used procedural language. Low to no dependencies. Room for advancement. Documented. Battle hardened. 😙🤌
