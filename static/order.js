



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
//action="/selected" method="POST"

function loadimg()
{
          imgFile =document.getElementById("myFile");
          document.getElementById("img").src = URL.createObjectURL(event.target.files[0]);
          document.getElementById("img_name").setAttribute("value",imgFile.files.item(0).name);

}


