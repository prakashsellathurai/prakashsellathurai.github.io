---
layout: default
title: Essays
description:  list of essays written by prakash sellathurai
permalink: /essays/
---



<ul>
  {% for post in site.posts %}
    <li>
      <a  href="{{ post.url }}" title="{{ post.title }}">{{ post.title }}</a>
    </li>
  {% endfor %}
</ul>

