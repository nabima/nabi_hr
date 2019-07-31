# -*- coding: utf-8 -*-


from openerp.osv import fields, osv
from datetime import *
from dateutil.relativedelta import *
from openerp import api,models,fields as Fields,tools,SUPERUSER_ID,_
from openerp.exceptions import *
import logging
_log = logging.getLogger(__name__)


class demande_achat(models.Model):
    _name="demande.achat"
    _inherit = [ 'mail.thread', 'ir.needaction_mixin']
    _description = u"Demande d'achat" 
    
    @api.one
    def _get_depense(self):
        res = self.env['hr.bon.caisse'].search([('operation','=','%s,%s' % (self._name, self.id))])
        self.depense_id = res
    
    name =      Fields.Char("Ref",default = "/",copy=False)
    date=       Fields.Date("Date",track_visibility='onchange')
    demandeur=  Fields.Many2one("hr.employee","Demandeur",track_visibility='onchange')  
    state=      Fields.Selection([('new','Nouvelle'),('confirme',u'Confirmée'),('valide',u'Validée'),('refuse',u'Refusée'),('annule',u'Annulée'),('encours','Encours'),('termine','Terminée')],string="Etat",track_visibility='always',default="new")
    visa1=      Fields.Boolean("Visa responsable",track_visibility='onchange',copy=False)
    visa2=      Fields.Boolean(u"Visa téchnique",track_visibility='onchange',copy=False)
    nature=     Fields.Many2one('demande.achat.nature', "Nature",track_visibility='onchange')
    rubrique=   Fields.Many2one('demande.achat.rubrique',"Rubrique",track_visibility='onchange')
    note=       Fields.Text("Note",track_visibility='onchange')
    department = Fields.Many2one('hr.department',u"Département")
    agence=     Fields.Many2one('hr.agence',"agence",required=True)
    fonction=   Fields.Many2one('hr.job',"Fonction")
    line=       Fields.One2many("demande.achat.line",'parent',"Lignes",track_visibility='onchange')
    valid_tech= Fields.Boolean("validation technique requise")
    depense_id = Fields.One2many('hr.bon.caisse',string=u'N° de dépense',compute=_get_depense)
    
    def user(self,cr,uid,ids,context=None):
        return self.pool['res.users'].browse(cr,SUPERUSER_ID,uid)
        
    @api.onchange('demandeur')
    def onchange_user(self):
        self.department = self.demandeur.department_id.id
        self.fonction = self.demandeur.job_id.id
    
    @api.onchange('nature')
    def onchange_nature(self):
        self.rubrique = False
    
    @api.onchange('rubrique')
    def onchange_rubrique(self):
        
        self.valid_tech = False
        if self.rubrique.valid_tech==True:
            self.valid_tech = True
    
    def unlink(self, cr, uid, ids, context=None):
        order = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in order:
            if s['state'] in ['new', 'annule']:
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid Action!'), "Avant de supprimer une demande vous devez l'annuler d'abord'!")

        return super(demande_achat, self).unlink(cr, uid, unlink_ids, context=context)


    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            seq_id = self.pool['hr.agence'].browse(cr,SUPERUSER_ID,vals['agence']).sequence._ids
            vals['name'] = self.pool.get('ir.sequence').next_by_id(cr, SUPERUSER_ID, seq_id, context=context) or '/'
        new_id = super(demande_achat, self).create(cr, uid, vals, context=context)
        self.message_post(cr, uid, [new_id], body=u"Demande créée", context=context)
        return new_id

class demande_achat_line(models.Model):
    _name="demande.achat.line"
    
    parent =    Fields.Many2one('demande.achat',"Parent")
    article=    Fields.Char('Article')
    qte=        Fields.Float(u"Quantité")
    remarque=   Fields.Text("Observation")
    specification=   Fields.Text(u"Spécifications")

class demande_achat_nature(models.Model):
    _name= "demande.achat.nature"
    
    name=   Fields.Char("Nature")
    rubrique=   Fields.One2many('demande.achat.rubrique','nature','Rubrique')

class demande_achat_rubrique(models.Model):
    _name = "demande.achat.rubrique"
    
    nature=     Fields.Many2one('demande.achat.nature', "Nature")
    name=       Fields.Char("Rubrique")
    valid_tech= Fields.Boolean(u"Validation Téchnique requise")
    validator=  Fields.Many2one("hr.department", u"Validé par")

class hr_agence(models.Model):
    _name="hr.agence"
    name        = Fields.Char("Agence")
    code        = Fields.Char("Code agence")
    sequence    = Fields.Many2one('ir.sequence',u"Séquence",                 required=True)
    seq_bc      = Fields.Many2one('ir.sequence',u"Séquence bon de carburant",required=True)
    seq_dpc     = Fields.Many2one('ir.sequence',u"Séquence demande dépassement carburant",required=True)
    seq_dep     = Fields.Many2one('ir.sequence',u"Séquence Bon de caisse",required=True)
    seq_credit  = Fields.Many2one('ir.sequence',u"Séquence demande crédit",required=True)
    seq_avance  = Fields.Many2one('ir.sequence',u"Séquence demande d'avance",required=True)
    
    @api.model
    def _create_sequence(self, vals,sequence=False):
        """ Create new no_gap entry sequence for every new Journal"""
        prefix =  '%s-%s-' % (sequence, vals['code'])
        seq_name = vals['name'] + ' : %s' % sequence 
        seq = {
            'name': seq_name,
            'implementation': 'no_gap',
            'prefix': prefix,
            'padding': 4,
            'number_increment': 1,
            'use_date_range': True,
            'company_id':False,
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        return self.env['ir.sequence'].create(seq)
    
    @api.model
    def create(self,vals):
    
    
        if not vals.get('sequence'):
            vals.update({'sequence': self.sudo()._create_sequence(vals,'DA').id})
        if not vals.get('seq_bc'):
            vals.update({'seq_bc': self.sudo()._create_sequence(vals,'BC').id})
        
        if not vals.get('seq_dpc'):
            vals.update({'seq_dpc': self.sudo()._create_sequence(vals,'DPC').id})
            
        res = super(hr_agence,self).create(vals)
        return res
    
class hr_entite(models.Model):
    _name="hr.entite"
    name = Fields.Char(u"Entité")
    code=   Fields.Char("Code entité")
