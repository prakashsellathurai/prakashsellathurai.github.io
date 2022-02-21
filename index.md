---
layout: default
title: Home
description:  Home page for Prakash Sellathurai's website
---





<div class="avatar-container">
<img class="avatar"   width="360" height="360" alt="icon" src="{{'./assets/images/avatar.jpg' | relative_url}}" aria-label="avatar" />
</div>

Hello!  I'm
<h2 style="overflow: hidden;"> Prakash Sellathurai </h2>

<p>
I am a <strong>Software Engineer</strong> with background in computer vision and fullstack engineering. My current job status is unemployed; I am actively looking for job opportunities.
</p>

<p>
 In the past, I worked as a software engineer at GKFIT and a computer vision engineer at Bigthinx. 
In 2018, I co-founded an e-commerce platform ClothX (now archived). As of 2019, I have earned my undergraduate degree in Mechatronics engineering from Anna University.
</p>
<p>
Software engineering, Information Theory, Digital control and Electromechanical control systems interest me. As a hobby, I often build automation projects and software tools.
</p>


## Essays:
My latest Essays are
<ul>
  {% for post in site.posts %}
    <li>
      <a  href="{{ post.url }}"  title="{{ post.title }}">{{ post.title }}</a>
    </li>
  {% endfor %}
</ul>






## Projects:
{% assign repolimit = 6 %}
{% include repos.html  %}

For more Projects, check out  my  **[Github](https://github.com/prakashsellathurai)**  profile.

{% include bookshelf.html %}
## Academic paper:
Automatic Packing system for Hydrphonic substitutes [pdf](https://github.com/prakashsellathurai/ICRAET_conference_paper/blob/master/ICEARCAT_PAPER.pdf), [code](https://github.com/prakashsellathurai/OLE_MACHINE)

## Contact:
Email is the best way to reach me. <br> My email address is  &emsp;"**prakash&nbsp;sellathurai [at] gmail [dot] com**"&emsp;(no dots ,no hyphens).


## Elsewhere:
Find me on   [LinkedIN](https://www.linkedin.com/in/prakashsellathurai/) , [Github](https://github.com/prakashsellathurai)  , [Goodreads](https://www.goodreads.com/user/show/105903487-prakash-sellathurai) , [Twitter]( https://twitter.com/prakash1729brt) , [Stackoverflow](https://stackoverflow.com/users/8336491/prakash-sellathurai) , [Codechef](https://www.codechef.com/users/prakash1729brt) and [Leetcode](https://leetcode.com/prakashsellathurai/) 


