
import urllib.request, json 
from rich import print
import yaml
# with urllib.request.urlopen("https://api.github.com/users/prakashsellathurai/repos") as url:
#     data = json.loads(url.read().decode())

#     with open('./repos.json', 'w', encoding='utf-8') as f:
#         json.dump(data, f, ensure_ascii=False, indent=4)


with open('./repos.json', 'r') as f:
    data: list = json.load(f)
data.sort(key= lambda datum: datum['pushed_at'],reverse=True)
if data:
    yamldata = []
    for datum in data:
        yamldata.append({
            'name': datum['name'],
            'url': datum['html_url'],
            'desc': datum['description']
        })

    with open('../_data/repos.yml', 'w') as yaml_file:
        yaml.dump(yamldata, yaml_file, default_flow_style=False)