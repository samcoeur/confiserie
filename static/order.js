



document.addEventListener("DOMContentLoaded", () => {

     document.querySelector("#up").addEventListener('click',function(){
          document.getElementById("units").value = parseInt(document.getElementById("units").value) + 1;
          if (document.getElementById("units").value >= 20 ) {
              document.getElementById("units").value = '20';
          }
          units = parseInt(document.getElementById("units").value);
    document.querySelector('#total').value = units * document.getElementById('price').getAttribute('value');

      })
 document.querySelector("#down").addEventListener('click',function(){
     document.getElementById("units").value = parseInt(document.getElementById("units").value) - 1;
     if (document.getElementById("units").value <= 0 ) {
         document.getElementById("units").value = '0';
     }
     units = parseInt(document.getElementById("units").value);
     document.querySelector('#total').value = units * document.getElementById('price').getAttribute('value');
});
units = parseInt(document.getElementById("units").value);
document.querySelector('#total').value = units * document.getElementById('price').getAttribute('value');



 /* load imgae file */




});


function total()
{

 unit = document.getElementById("unit");
 unit.addEventListener('keyup', (e)=>{
      cost = unit.value * document.getElementById('price').getAttribute('value');
      cost = cost.toFixed(2);
      cost = Math.round(cost * 100) / 100
      total_cost = document.getElementById('total');
      total_cost.setAttribute('value', cost  );
     document.getElementById("units").setAttribute('value',unit.value);
    // document.getElementById("cost").setAttribute('value',cost);
 })
 unit.addEventListener('click', (e)=>{
     cost = unit.value * document.getElementById('price').getAttribute('value');
     cost = cost.toFixed(2);
     cost = Math.round(cost * 100) / 100
     total_cost = document.getElementById('total');
     total_cost.setAttribute('value',cost  );
     document.getElementById("units").setAttribute('value',unit.value);
})
}

function add()
{

     document.querySelectorAll('button').forEach(btn => {
          btn.addEventListener('click',(event)=>{

                    document.querySelectorAll('button').style.background = "blue";

          })
        })
}






document.addEventListener("DOMContentLoaded",()=>{

           cart_container = document.querySelector("#cart_container");
          document.querySelector("#cart").addEventListener('click', ()=>{
               if ( cart_container.style.display == "none" )
               {
               cart_container.style.display = 'block'
               }
               else
               {
               cart_container.style.display = 'none'
               }
          })



})

document.addEventListener("DOMContentLoaded",()=>{

     document.querySelector("#finalize").addEventListener("click",()=>{
          document.querySelector("#method").value = document.querySelector("#delivery").value;
          document.querySelector("#form_cart").submit;
     })

})