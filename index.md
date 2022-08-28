---
layout: default
title: Prakash Sellathurai
description:  Home page
---

<style>
.h2links {
  display: flex;
  align-items: center;
}
.h2links > a{
  color: var(--content);  
}
.h2links:after {
  content: '';
  flex: 1;
  margin-left: 1rem;
  height: 1px;
  background-color: #bfbfbf;
}

</style>

<div class="avatar-container">
  <picture>
    <source media="(max-width:600px)" srcset="{{'./assets/images/avatar526.jpg' | relative_url}}">
    <img class="avatar"   width="128" height="128" alt="icon" aria-label="avatar" src="{{'./assets/images/avatar.jpg' | relative_url}}"  />
</picture>

</div>

<div style="margin-top: 1.5em;">Hello!  I'm <h1 style="font-style: inherit;font-size: inherit;display: inline">Prakash</h1></div>

<p>
I am a Software Engineer from an interdisciplinary (Mechatronics) background primarily focused on Computer Vision, and Python, with a solid foundation in coding, testing, code reviews and other software engineering practices.
</p>

<p>
Currently, I am a software development Engineer at Amazon. In the past, I worked as a <strong>Software engineer</strong> at Gkfit and a Computer Vision Engineer at Bigthinx. 
In 2018, I co-founded an e-commerce platform ClothX (now archived). As of 2019, I have earned my undergraduate degree in Mechatronics Engineering from Anna University.
</p>
<p>
My interests lie in the fields of software engineering, information theory, digital control, and electromechanical control systems. I enjoy building automation projects and developing software.
</p>








<h2 class="h2links"><a href="#projects">Projects</a></h2>
{% assign repolimit = 6 %}
{% include repos.html  %}

For more Projects, check out  my  **[Github](https://github.com/prakashsellathurai)**  profile.

<h2 class="h2links"><a href="#essays">Essays</a></h2>
My latest Essays are
{% for post in site.posts %}
  - [{{ post.title }}]({{  post.url }})
{% endfor %}



{% include bookshelf.html %}

<h2 class="h2links"><a href="#contact">Contact</a></h2>
Email is the best way to reach me.  My email address is "**prakash&nbsp;sellathurai [at] gmail [dot] com**".

<h2 class="h2links"><a href="#elsewhere">Elsewhere</a></h2>
Find me on   [LinkedIN](https://www.linkedin.com/in/prakashsellathurai/), [Github](https://github.com/prakashsellathurai), [Goodreads](https://www.goodreads.com/user/show/105903487-prakash-sellathurai), [Twitter]( https://twitter.com/prakash1729brt), [Stackoverflow](https://stackoverflow.com/users/8336491/prakash-sellathurai), [Codechef](https://www.codechef.com/users/prakash1729brt) and [Leetcode](https://leetcode.com/prakashsellathurai/) 


