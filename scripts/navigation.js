$(document).ready(function(){$(".nav__open-links").click(function(n){$(".nav__links").is(":hidden")?($(".nav__links").slideDown(300,function(){$(this).css("display","block")}),$(this).addClass("active")):($(".nav__links").slideUp(300,function(){$(this).css("display","none")}),$(this).removeClass("active"))}),$(document).mouseup(function(n){$(".nav__open-links").is(n.target)||$(".nav__links").is(n.target)||0!==$(".nav__links").has(n.target).length||!$(".nav__open-links").is(":visible")||($(".nav__open-links").removeClass("active"),$(".nav__links:visible").slideUp(300,function(){$(this).css("display","none")}))}),$(window).resize(function(){$(".nav__open-links").is(":visible")||($(".nav__links").removeAttr("style"),$(".nav__open-links").removeClass("active"))})});