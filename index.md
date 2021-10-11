---
layout: default
title: Home
description:  Home page for Prakash Sellathurai's website
---

<style>

.home-cards {
     display:grid;
     max-width: 100%;
     grid-template-columns: 1fr 3fr;
     grid-column-gap: 20px;
     grid-row-gap: 20px;
     justify-items: stretch;
     

}
.home-card{
     min-height: 40px;
}
@media (max-width: 400px) {
  .home-cards {
    grid-template-columns: 1fr;
  }
  .home-cards img.avatar {
       width: 40%;
  }
}
</style>

<div class="home-cards">
 <div class="home-card">
     {% include avatar.html %}
</div>
 <div class="home-card">
     <span><strong>Bio</strong></span><br>
     Prakash Sellathurai is an Software Engineer, experienced with technologies focused on Computer Vision and Deep Learning.
</div>
</div>


He finished his Mechatronics engineering undergraduate degree on 2019.He is proficient in Python , C++ ,and  have strong foundation in both Algorithms and Data Structures.

**Mail me at:**
     MyFirstName MyLastName (at) gmail (dot) com


**Social Links:**

- [LinkedIN](https://www.linkedin.com/in/prakashsellathurai/)
- [Github](https://github.com/prakashsellathurai)
- [Goodreads](https://www.goodreads.com/user/show/105903487-prakash-sellathurai)
- [Twitter]( https://twitter.com/prakash1729brt)
- [Stackoverflow](https://stackoverflow.com/users/8336491/prakash-sellathurai)


