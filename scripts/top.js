!function($){"use strict";$(document).ready(function(){var a=document.querySelector(".progress-wrap path"),b=a.getTotalLength();a.style.transition=a.style.WebkitTransition="none",a.style.strokeDasharray=b+" "+b,a.style.strokeDashoffset=b,a.getBoundingClientRect(),a.style.transition=a.style.WebkitTransition="stroke-dashoffset 10ms linear";var c=function(){var c=$(window).scrollTop(),d=$(document).height()-$(window).height();a.style.strokeDashoffset=b-c*b/d};c(),$(window).scroll(c),jQuery(window).on("scroll",function(){jQuery(this).scrollTop()>50?jQuery(".progress-wrap").addClass("active-progress"):jQuery(".progress-wrap").removeClass("active-progress")}),jQuery(".progress-wrap").on("click",function(a){return a.preventDefault(),jQuery("html, body").animate({scrollTop:0},550),!1})})}(jQuery)