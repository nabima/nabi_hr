# -*- coding: utf-8 -*-


from openerp.osv import fields, osv
from datetime import *
from dateutil.relativedelta import *
from openerp import api,models,fields as Fields,tools,SUPERUSER_ID,_
from openerp.exceptions import *
import logging
_log = logging.getLogger(__name__)


class bon_carburant(models.Model):
    _name = "bon.carburant"
    _description = u"Bon de carburant moyens généraux"
    _inherit = [ 'mail.thread', 'ir.needaction_mixin']
    
    date        = Fields.Date("Date",track_visibility='onchange')
    name        = Fields.Char(u"Réf.", default="/",copy=False)
    chauffeur   = Fields.Many2one("hr.employee","Nom du chauffeur",track_visibility='onchange')
    vehicle     = Fields.Many2one("fleet.vehicle",u"Véhicule")
    liter       = Fields.Float("Nombre de litres")
    amount      = Fields.Float(u"Montant demandé",track_visibility='onchange')
    ref_bt      = Fields.Char(u"No. du Tableau récapitulatif des BT relatifs")
    state       = Fields.Selection([('new','Nouveau'),('confirme',u'Confirmée'),('valide',u'Validée'),('annule',u'Annulée'),('refuse',u'Refusée'),('termine',u'Terminée')],string="Etat",default="new",copy=False,track_visibility='onchange')
    visa1       = Fields.Boolean(u"Visa chargé du transport",track_visibility='onchange',copy=False)
    visa2       = Fields.Boolean(u"Visa resp. départ.",track_visibility='onchange',copy=False)
    agence=     Fields.Many2one('hr.agence',"Agence",required=True)
    no_bon      = Fields.Char(u"Réferences",track_visibility='onchange')
    rendu       = Fields.Float(u"Rendu",track_visibility='onchange')
    mtt_cons    = Fields.Float(u"Montant consommé",track_visibility='onchange')
    
    @api.one
    def _get_depense(self):
        res = self.env['hr.bon.caisse'].search([('operation','=','%s,%s' % (self._name, self.id))])
        self.depense_id = res
    
    depense_id = Fields.One2many('hr.bon.caisse',string=u'N° de dépense',compute=_get_depense)
    
    
    
    def user(self,cr,uid,ids,context=None):
        return self.pool['res.users'].browse(cr,1,uid)
        
    def uunlink(self, cr, uid, ids, context=None):
        order = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in order:
            if s['state'] in ['new', 'annule']:
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid Action!'), u"Avant de supprimer une demande vous devez l'annuler d'abord!")

        return super(bon_carburant, self).unlink(cr, uid, unlink_ids, context=context)


    def create(self, cr, uid, vals, context=None):
        
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            seq_id = self.pool['hr.agence'].browse(cr,SUPERUSER_ID,vals['agence']).seq_bc._ids
            vals['name'] = self.pool.get('ir.sequence').next_by_id(cr, SUPERUSER_ID, seq_id, context=context) or '/'
        new_id = super(bon_carburant, self).create(cr, uid, vals, context=context)
        self.message_post(cr, uid, [new_id], body=u"Demande créée", context=context)
        return new_id
        
        
class demande_depassement_carburant(models.Model):
    _name = "demande.depassement.carburant"
    _description = u"Demande de dépassement du plafond de carburant"
    _inherit = [ 'mail.thread', 'ir.needaction_mixin']
    
    date        = Fields.Date("Date",track_visibility='onchange')
    name        = Fields.Char(u"Réf.", default="/",copy=False)
    chauffeur   = Fields.Many2one("hr.employee","Nom du chauffeur",track_visibility='onchange')
    departement = Fields.Many2one("hr.department",u"Département")
    vehicle     = Fields.Many2one("fleet.vehicle",u"Véhicule",track_visibility='onchange')
    liter       = Fields.Float("Nombre de litres")
    amount      = Fields.Float(u"Montant demandé",track_visibility='onchange')
    ref_bt      = Fields.Char(u"No. du Tableau récapitulatif des BT relatifs")
    state       = Fields.Selection([('new','Nouveau'),('confirme',u'Confirmée'),('valide',u'Validée'),('annule',u'Annulée'),('refuse',u'Refusée'),('termine',u'Terminée')],string="Etat",default="new",copy=False,track_visibility='onchange')
    visa1       = Fields.Boolean(u"Visa resp. département",track_visibility='onchange',copy=False)
    visa2       = Fields.Boolean(u"Visa resp. départ.",track_visibility='onchange',copy=False)
    agence      = Fields.Many2one('hr.agence',"Agence",required=True)
    montant_accord=Fields.Float(u"Montant Accordé",track_visibility='onchange')
    ordre_mission= Fields.Char(u"No. ordre de mission")
    mtt_odm     = Fields.Float(u"Montant de l'ordre de mission")
    
    @api.one
    def _get_depense(self):
        res = self.env['hr.bon.caisse'].search([('operation','=','%s,%s' % (self._name, self.id))])
        self.depense_id = res
    depense_id = Fields.One2many('hr.bon.caisse',string=u'N° de dépense',compute=_get_depense)
    
    @api.onchange('chauffeur')
    def onchange_all(self):
        self.department = self.chauffeur and self.chauffeur.department_id and self.chauffeur.department_id.id        
    def user(self,cr,uid,ids,context=None):
        return self.pool['res.users'].browse(cr,1,uid)
        
    def uunlink(self, cr, uid, ids, context=None):
        order = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in order:
            if s['state'] in ['new', 'annule']:
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid Action!'), u"Avant de supprimer une demande vous devez l'annuler d'abord'!")

        return super(demande_depassement_carburant, self).unlink(cr, uid, unlink_ids, context=context)


    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            seq_id = self.pool['hr.agence'].browse(cr,SUPERUSER_ID,vals['agence']).seq_dpc._ids
            vals['name'] = self.pool.get('ir.sequence').next_by_id(cr, SUPERUSER_ID, seq_id, context=context) or '/'
        new_id = super(demande_depassement_carburant, self).create(cr, uid, vals, context=context)
        self.message_post(cr, uid, [new_id], body=u"Demande créée", context=context)
        return new_id
