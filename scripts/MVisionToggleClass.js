! function(t) {
    t.fn.MVisionToggleClass = function(a) {
        a = t.extend({
            classButton: "class-button",
            toggleClassButton: "new-class-button",
            dataButtonAttr: "data-button",
            classBox: "class-box",
            toggleClassBox: "new-class-box",
            dataBoxAttr: "data-box",
            cancelOutside: !1,
            cancelRepeat: !1,
            defaultElement: !1,
            defaultIndexElement: 0,
            ancoreLinks: !1,
            ancoreParent: !1
        }, a);
        var s = {
            btn: t(this).find("." + a.classButton + "[" + a.dataButtonAttr + "]"),
            box: t(this).find("." + a.classBox + "[" + a.dataBoxAttr + "]"),
            anc: window.location.hash.replace("#", "")
        };
        console.log(window.location.hash), a.ancoreLinks && s.anc && (a.ancoreParent && t("*[data-name-tab = " + a.ancoreParent + "]").length > 0 && t("*[data-name-tab=" + a.ancoreParent + "]").find("." + a.classBox + "[data-name-tab=" + s.anc + "]").length > 0 && (t("*[data-open-tab = " + a.ancoreParent + "]").addClass("active"), t("*[data-name-tab = " + a.ancoreParent + "]").addClass("active")), s.btn.length > 0 && s.box.length > 0 && (s.btn.each(function() {
            t(this).attr(a.dataButtonAttr) == s.anc && (s.btn.removeClass(a.toggleClassButton), t(this).addClass(a.toggleClassButton))
        }), s.box.each(function() {
            t(this).attr(a.dataBoxAttr) == s.anc && (s.box.removeClass(a.toggleClassBox), t(this).addClass(a.toggleClassBox))
        }))), a.defaultElement && !s.anc && (s.btn.eq(a.defaultIndexElement).addClass(a.toggleClassButton), s.box.eq(a.defaultIndexElement).addClass(a.toggleClassBox)), s.btn.css("cursor", "pointer"), s.btn.click(function(e) {
            if (e.preventDefault(), t(this).hasClass(a.toggleClassButton)) a.cancelRepeat && (s.btn.removeClass(a.toggleClassButton), s.box.removeClass(a.toggleClassButton));
            else {
                var n = t(this).attr(a.dataButtonAttr);
                s.btn.removeClass(a.toggleClassButton), t(this).addClass(a.toggleClassButton), s.box.removeClass(a.toggleClassBox), t("." + a.classBox + "[" + a.dataBoxAttr + " = " + n + "]").addClass(a.toggleClassBox), a.ancoreLinks && (window.location.hash = "#" + t(this).attr(a.dataButtonAttr))
            }
        }), a.cancelOutside && t(document).mousedown(function(t) {
            s.box.is(t.target) || 0 !== s.box.has(t.target).length || s.btn.is(t.target) || 0 !== s.btn.has(t.target).length || (s.btn.removeClass(a.toggleClassButton), s.box.removeClass(a.toggleClassButton))
        })
    }
}(jQuery);