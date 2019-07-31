# -*- coding: utf-8 -*-
from openerp.osv import osv, fields
from openerp import api,fields as Fields


class mg_stock_operation(osv.osv):
    _name           =  "mg.stock.operation"
    _description    = u"Oprération  de stock"
    
    _columns = {
        'name':     fields.char("Name", default="/",copy=False),
        'date':    fields.date("Date" ,oldname="date "),
        'state':    fields.selection([('new'   ,'Nouveau'),
                                      ('valide',u'Validé'),
                                      ('cancel',u'Annulé')],"Etat", default="new",copy=False),
        'commande': fields.many2one('purchase.order',"Commande"),
        'Origin':   fields.char("Origin"),
        'line':     fields.one2many("mg.stock.operation.line","parent_id","Lignes", copy=True),
        'type':     fields.selection([  ('in'        ,u'Réception'),
                                        ('in_return' ,u'retour fournisseur'),
                                        ('out'       ,u'Sortie'),
                                        ('out_return',u'Retours'),
                                        ], string=u"Type d'opération"),
        'note':         fields.text("Note"),
        'employee':     fields.many2one("hr.employee",u"Employée"),
        'emplacement':  fields.many2one("mg.stock.emplacement","Stock"),
        'agence':       fields.many2one("hr.agence","Agence"),
        }

    def create(self, cr, uid, values, context=None):
     
        extid_obj = self.pool['ir.model.data']
        if 'agence' in values and values['agence']:
            code_agence = self.pool['hr.agence'].browse(cr,uid,values['agence']).code
        else:   
            raise osv.except_osv("Error","Agence Obligatoire !")
    
        if 'name' in values and values['name'] == '/':
            sequence = extid_obj.get_object(cr,uid,'nabi_hr','sequence_stock_mg_%s' % values['type'])
            name = sequence._next()
            values['name'] = name.replace('-',"-%s-" % code_agence,1)
            
        
        res = super(mg_stock_operation, self).create(cr,uid,values,context=context)
    
        return res
    
    
    def action_valide(self,cr, uid,ids,context=None):
        stock = self.pool['mg.stock']
        for obj in self.browse(cr, uid,ids,context=context).filtered(lambda x:x.state == 'new'):
            for l in obj.line:
                stock_ids = stock.search(cr,uid,[('article','=',l.article.id),('emplacement','=',obj.emplacement.id)])
                if not stock_ids:
                    stock_ids = stock.create(cr,uid,{'emplacement':obj.emplacement.id, 'article':l.article.id, 'qte':0})
                
                stock_actuel = stock.browse(cr,uid,stock_ids).qte
                
                
                #Entree en stock
                if obj.type in ('in','out_return'):
                    stock.write(cr,uid,stock_ids,{'qte': l.qte + stock_actuel})
                
                # sortie de stock
                if obj.type in ('out', 'in_return'):
                    if stock_actuel < l.qte :
                        raise osv.except_osv('Error','Stock disponible insuffisant')
                    stock.write(cr,uid,stock_ids,{'qte':  stock_actuel - l.qte })
                # end boucle ligne
            
            obj.state = 'valide'
            # end boucle entete
            

        return True 
    
    
    
class mg_stock_operation_line(osv.osv):
    _name           =  "mg.stock.operation.line"
    _description    = u" Line oprération  de stock"
    
    def _get_disp(self,cr,uid,ids,fields, arg,context=None):
        res = {}
        for o in self.browse(cr,uid,ids):
            line_stock = o.parent_id.emplacement.stock
            qte_dispo = sum([x.qte for x in line_stock  if x.article.id == o.article.id])
            res[o.id]  = qte_dispo or 0
        return res
            
    
    _columns        = {
        'article' : fields.many2one('product.product','Article'),
        'qte':fields.float(u'Quantité'),
        'parent_id' : fields.many2one('mg.stock.operation','Parent'),
        'disponible': fields.function(_get_disp, string="Stock dispo." , type="float"),
        }


class mg_stock(osv.osv):
    _name = "mg.stock"
    
    _columns ={
        'emplacement' : fields.many2one('mg.stock.emplacement','Stock'),
        'article' : fields.many2one('product.product','Article'),
        'qte':fields.float(u'Quantité'),
    }
    

class mg_stock_emplacement(osv.osv):
    _name ="mg.stock.emplacement"
    _columns ={
        'name':	         fields.char("Name", required=True),
        'responsable' :  fields.many2one("res.users",'Responsable'),
        'stock':   fields.one2many("mg.stock","emplacement","Stock" , oldname="emplacement"),
        'agence':        fields.many2one("hr.agence","Agence"),
    }
    

class mg_bon_affectation(osv.osv):
    _name='mg.bon.affectation'
    _columns ={
        'name':     fields.char("Nom"),
        'employee': fields.many2one("hr.employee",u"Employée"),
        'line':     fields.one2many("mg.bon.affectation.line", "parent_id", "Lignes"),
        'date':     fields.date("date"),
        'agence':   fields.many2one("hr.agence","Agence"),
        'state':    fields.selection([('new','Nouveau'),('valide',u'Validé')],string="State", default='new'),
        'note':     fields.text("Note"),
        
    }
    
    def create(self, cr, uid, values, context=None):
    
        res = super(mg_bon_affectation,self).create(cr,uid,values,context=context)
        return res
    
    
    
    
    
class mg_bon_affectation_line(osv.osv):
    _name='mg.bon.affectation.line'
    _columns ={
        'parent_id' :fields.many2one('mg.bon.affectation', 'Parent'),
        'article' : fields.many2one('product.product','Article'),
        'qte':fields.float(u'Quantité'),
        'note':     fields.text("Note"),
        }
    



