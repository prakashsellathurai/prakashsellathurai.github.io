---
layout: default
title: Projects
---


<div class="d-sm-flex flex-wrap gutter-condensed mb-4">
  {% if site.projects.sort_by == 'stars' %}
    {% assign sort_order = 'stargazers_count' %}
  {% else %}
    {% assign sort_order = 'pushed_at' %}
  {% endif %}

  {% if site.projects.exclude.archived and site.projects.exclude.forks %}
    {% assign filtered_repos = site.github.public_repositories | where:'archived', false | where:'fork', false | sort: sort_order | reverse %}
  {% elsif site.projects.exclude.archived %}
    {% assign filtered_repos = site.github.public_repositories | where:'archived', false | sort: sort_order | reverse %}
  {% elsif site.projects.exclude.forks %}
    {% assign filtered_repos = site.github.public_repositories | where:'fork', false | sort: sort_order | reverse %}
  {% else %}
    {% assign filtered_repos = site.github.public_repositories | sort: sort_order | reverse %}
  {% endif %}

  {% for repository in filtered_repos  limit: site.projects.limit %}
    {% unless site.projects.exclude.projects contains repository.name %}
      
        {% include repo-card.html %}
      
    {% endunless %}
  {% endfor %}
</div>