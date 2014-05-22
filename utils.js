function exprToString(expr, display_scopes) {
    //console.log(typeof expr);
    if (expr instanceof Array) {
        if (expr[0] === "scope_include" && !display_scopes) {
            return exprToString(expr[3]);
        } else {
            return "(" + expr.map(function (e) { return exprToString(e, display_scopes) }).join(" ") + ")";
        }
    } else if (typeof expr === "string") {
        return expr;
    } else {
        return expr.value.toString();
    }
}

function directiveToString(directive, display_scopes) {
    var directive_str = "[" + directive.instruction + " ";
    
    if (directive.instruction === "assume") {
        directive_str += directive.symbol + " ";
    }
    
    directive_str += exprToString(directive.expression, display_scopes);
    
    if (directive.instruction === "observe") {
        directive_str += " " + directive.value.toFixed(2);
    }
    
    directive_str += "]";
    directive_str = directive_str.replace(/add/g, "+")
    directive_str = directive_str.replace(/sub/g, "-")
    directive_str = directive_str.replace(/mul/g, "*")
    directive_str = directive_str.replace(/div/g, "/")
    return directive_str;
}

blacklist = ['demo_id', 'model_type', 'use_outliers', 'infer_noise', 'outlier_prob', 'show_scopes', 'outlier_sigma'];

function isExtraneous(directive) {
    if (directive.instruction === "predict") return true;
    if (directive.instruction === "assume") {
        return blacklist.indexOf(directive.symbol) >= 0;
    }
    return false;
}

function VentureCodeHTML(directives, display_scopes) {
    var venture_code_str = "<b>Venture code:</b><br>";

    for (i = 0; i < directives.length; ++i) {
        if(!isExtraneous(directives[i])) {
            venture_code_str += directiveToString(directives[i], display_scopes) + '<br/>';
        }
    }
    
    return venture_code_str;
}

