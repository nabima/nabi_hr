# -*- coding: utf-8 -*-


from openerp.osv import fields, osv
from datetime import *
from dateutil.relativedelta import *
from openerp import api,models,fields as Fields,tools,SUPERUSER_ID,_
from openerp.exceptions import *
import logging
_log = logging.getLogger(__name__)


class bureau_ordre(osv.osv):
    _name ="bureau.ordre"
    _description = "Bureau d'ordre"
    _columns = {
    
        'type'      : fields.many2one("bureau.ordre.type","Type"),
        'ttc'       : fields.float("Montant TTC"),
        'state'     : fields.selection([('new','Nouveau'),('confirmed','Confirmé'),('progress','En cours'),('done','Terminé')],string="Etat",default='new'),
        'partner_id': fields.many2one('res.partner',"Fournisseur"),
        'name'      : fields.char("Nom"),
        'date_rec'  : fields.date("date de réception"),
        'date_fact' : fields.date("Date de facture"),
        'check_list': fields.one2many("bureau.ordre.type.checklist","type","Checklist"),
        
    }
    

class bureau_ordre_type(osv.osv):
    _name ="bureau.ordre.type"
    _description = "Bureau d'ordre :: Type"
    _columns = {
    
        'name'          : fields.char("Nom"),
        'check_list'    : fields.one2many("bureau.ordre.type.checklist","type","Checklist"),
        
    }
    
class bureau_ordre_type_check_list(osv.osv):
    _name ="bureau.ordre.type.checklist"
    _description = "Bureau d'ordre :: checklist"
    _columns = {
    
        'name'  : fields.char("Nom"),
        'type'  : fields.many2one("bureau.ordre.type","Type"),
        
    }
