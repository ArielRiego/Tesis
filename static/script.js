const allDropdown = document.querySelectorAll('#sidebar .side-dropdown');

allDropdown.forEach(item=> {
    const a = item.parentElement.querySelector('a:first-child');
    a.addEventListener('click',function(e){
        e.preventDefault();
        

        
        /* Hace que varios botones desplegables se queden abiertos al mismo tiempo, si saco el ! solo 
        abre uno a la vez */
        if(!this.classList.contains('activo')){

            allDropdown.forEach(i=> {
                const aLink = i.parentElement.querySelector('a:first-child');
                aLink.classList.remove ('activo');
                i.classList.remove ('show');

            })
        }
        
        /* para desplegar los botones del menu */
        this.classList.toggle ('activo');
        item.classList.toggle ('show');
    })
})