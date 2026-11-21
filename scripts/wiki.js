function toggleController(t,e,o){$(t+" > "+e).click(function(t){$(this).parent().find(o).slideToggle(),$(this).toggleClass("active")})}toggleController(".spoiler",".spoiler__header",".spoiler__content"),$(".wiki").MVisionToggleClass({classButton:"wiki__nav-item",toggleClassButton:"active",dataButtonAttr:"data-open-tab",classBox:"wiki__content",toggleClassBox:"active",dataBoxAttr:"data-name-tab",defaultElement:!0,defaultIndexElement:0,ancoreLinks:!0});
// On phones the tabs are one horizontal strip (main.css): keep the picked tab visible in it.
$(".wiki__nav").each(function () {
  var nav = this, active = nav.querySelector(".wiki__nav-item.active");
  if (active) nav.scrollLeft = active.offsetLeft - (nav.clientWidth - active.offsetWidth) / 2;
});
$(document).on("click", ".wiki__nav-item", function () {
  var nav = this.parentElement;
  if (nav.scrollWidth > nav.clientWidth) $(nav).animate({ scrollLeft: this.offsetLeft - (nav.clientWidth - this.offsetWidth) / 2 }, 200);
});
