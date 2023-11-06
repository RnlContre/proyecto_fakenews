var resultado = document.getElementById('mensaje');

function cambiarColor(resultado){
    if(resultado.value == "La noticia es verdadera"){
        resultado.style.background = 'green';
    }else{
        resultado.style.background = 'red';
    }
}