from flask import Blueprint,render_template,request,redirect,session,jsonify,make_response
from .database.db import get_db
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
main=Blueprint('main',__name__)
def auth(): return 'uid' in session
@main.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  c=get_db();u=c.execute('select * from users where username=? and password=?',(request.form['username'],request.form['password'])).fetchone()
  if u:session.update(uid=u['id'],username=u['username'],role=u['role']);return redirect('/')
  return render_template('login.html',error='Invalid username or password')
 return render_template('login.html')
@main.route('/logout')
def logout():session.clear();return redirect('/login')
@main.route('/')
def dashboard():
 if not auth():return redirect('/login')
 c=get_db();stats={'sales':c.execute("select coalesce(sum(total),0)n from invoices where date(created_at)=date('now')").fetchone()['n'],'orders':c.execute("select count(*)n from invoices where date(created_at)=date('now')").fetchone()['n'],'products':c.execute('select count(*)n from products').fetchone()['n'],'low':c.execute('select count(*)n from products where stock<=min_stock').fetchone()['n']};recent=c.execute("select i.*,coalesce(c.name,'Walk-in Customer')customer from invoices i left join customers c on c.id=i.customer_id order by i.id desc limit 7").fetchall();return render_template('dashboard.html',stats=stats,recent=recent,page='dashboard')
@main.route('/billing')
def billing():
 if not auth():return redirect('/login')
 c=get_db();return render_template('billing.html',products=c.execute('select * from products order by name').fetchall(),customers=c.execute('select * from customers order by name').fetchall(),page='billing')
@main.route('/api/products')
def products_api():
 if not auth():return jsonify(error='Unauthorized'),401
 q=request.args.get('q','');c=get_db();return jsonify([dict(r) for r in c.execute('select * from products where name like ? or sku like ? order by name',('%'+q+'%','%'+q+'%')).fetchall()])
@main.route('/api/invoice',methods=['POST'])
def create_invoice():
 if not auth():return jsonify(error='Unauthorized'),401
 d=request.get_json();items=d.get('items',[])
 if not items:return jsonify(error='Cart is empty'),400
 c=get_db();sub=gst=0
 for x in items:
  p=c.execute('select * from products where id=?',(x['id'],)).fetchone()
  if not p or x['qty']>p['stock']:return jsonify(error='Insufficient stock'),400
  sub+=p['price']*x['qty'];gst+=p['price']*x['qty']*p['gst']/100
 discount=float(d.get('discount',0));total=max(0,sub-discount+gst);no='INV-'+datetime.now().strftime('%Y%m%d-%H%M%S');cur=c.execute('insert into invoices(invoice_no,customer_id,subtotal,discount,gst,total,payment) values(?,?,?,?,?,?,?)',(no,d.get('customer_id') or None,sub,discount,gst,total,d.get('payment','Cash')));iid=cur.lastrowid
 for x in items:
  p=c.execute('select * from products where id=?',(x['id'],)).fetchone();c.execute('insert into invoice_items(invoice_id,product_id,qty,price,gst) values(?,?,?,?,?)',(iid,p['id'],x['qty'],p['price'],p['price']*x['qty']*p['gst']/100));c.execute('update products set stock=stock-? where id=?',(x['qty'],p['id']))
 c.commit();return jsonify(success=True,id=iid)
@main.route('/invoices')
def invoices():
 if not auth():return redirect('/login')
 c=get_db();return render_template('invoices.html',invoices=c.execute("select i.*,coalesce(c.name,'Walk-in Customer')customer from invoices i left join customers c on c.id=i.customer_id order by i.id desc").fetchall(),page='invoices')
@main.route('/invoice/<int:iid>')
def invoice(iid):
 if not auth():return redirect('/login')
 c=get_db();inv=c.execute("select i.*,coalesce(c.name,'Walk-in Customer')customer,c.phone,c.email from invoices i left join customers c on c.id=i.customer_id where i.id=?",(iid,)).fetchone();items=c.execute('select ii.*,p.name,p.sku from invoice_items ii join products p on p.id=ii.product_id where ii.invoice_id=?',(iid,)).fetchall();return render_template('invoice.html',inv=inv,items=items,page='invoices')
@main.route('/invoice/<int:iid>/pdf')
def pdf(iid):
 c=get_db();inv=c.execute("select i.*,coalesce(c.name,'Walk-in Customer')customer from invoices i left join customers c on c.id=i.customer_id where i.id=?",(iid,)).fetchone();items=c.execute('select ii.*,p.name from invoice_items ii join products p on p.id=ii.product_id where ii.invoice_id=?',(iid,)).fetchall();b=BytesIO();p=canvas.Canvas(b,pagesize=A4);w,h=A4;p.setFont('Helvetica-Bold',22);p.drawString(45,h-55,'BILLPRO');p.setFont('Helvetica',10);p.drawString(45,h-72,'Smart Commerce Billing');p.drawRightString(w-45,h-55,inv['invoice_no']);y=h-120;p.setFont('Helvetica-Bold',11);p.drawString(45,y,'Bill To: '+inv['customer']);y-=35;p.setFont('Helvetica-Bold',10);p.drawString(45,y,'Item');p.drawString(350,y,'Qty');p.drawRightString(w-45,y,'Amount');y-=25
 for x in items:p.setFont('Helvetica',10);p.drawString(45,y,x['name'][:45]);p.drawString(350,y,str(x['qty']));p.drawRightString(w-45,y,f"Rs.{x['price']*x['qty']+x['gst']:,.2f}");y-=22
 y-=10;p.setFont('Helvetica-Bold',13);p.drawRightString(w-45,y,f"TOTAL  Rs.{inv['total']:,.2f}");p.save();b.seek(0);r=make_response(b.read());r.headers['Content-Type']='application/pdf';return r
@main.route('/products',methods=['GET','POST'])
def product_page():
 if not auth():return redirect('/login')
 c=get_db()
 if request.method=='POST':
  f=request.form
  try:c.execute('insert into products(name,sku,category,price,cost,stock,min_stock,gst) values(?,?,?,?,?,?,?,?)',(f['name'],f['sku'],f['category'],f['price'],f['cost'],f['stock'],f['min_stock'],f['gst']));c.commit()
  except:pass
  return redirect('/products')
 return render_template('products.html',products=c.execute('select * from products order by id desc').fetchall(),page='products')
@main.route('/customers',methods=['GET','POST'])
def customer_page():
 if not auth():return redirect('/login')
 c=get_db()
 if request.method=='POST':
  f=request.form;c.execute('insert into customers(name,phone,email,address) values(?,?,?,?)',(f['name'],f['phone'],f['email'],f['address']));c.commit();return redirect('/customers')
 return render_template('customers.html',customers=c.execute('select * from customers order by id desc').fetchall(),page='customers')
