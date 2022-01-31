---
layout: default
title: Projects
description:   list of Projects by Prakash Sellathurai
permalink: /projects/
---


<div class="d-sm-flex flex-wrap gutter-condensed mb-4">
  {% for repository in site.data.repos %}
        {% include repo-card.html %}
  {% endfor %}
</div>