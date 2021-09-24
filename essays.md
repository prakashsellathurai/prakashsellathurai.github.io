---
layout: default
title: Essays
showTitle: true
---



<ul>
  {% for post in site.posts %}
    <li>
      <a  style="text-decoration: none;" href="{{ post.url }}">{{ post.title }}</a>
    </li>
  {% endfor %}
</ul>

