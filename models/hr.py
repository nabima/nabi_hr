# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp.osv import fields, osv
from openerp     import api, models, fields as Fields
from openerp.tools import float_compare, float_round
from openerp.tools.translate import _
from datetime import *
from dateutil.relativedelta import *
from openerp import tools
from datetime import datetime as dt



from openerp import SUPERUSER_ID, api, fields as Fields,models

import logging
_logger = logging.getLogger(__name__)


class hr_employee(osv.osv):
    _inherit = "hr.employee"
    
    _columns = {
        'matricule':        fields.char(string=u"Matricule"),
        'affectation':      fields.char(string=u"Affectation"),
        'agence':	        fields.char(string=u"Agence"),
        'date_embauche':    fields.date(string=u"Date D'embauche"),
        'anciennete':       fields.float(string=u"Ancienneté"),
        'date_declaration': fields.date(string=u"Date de déclaration"),
        'age':              fields.float(string=u"Age"),
        'date_expiration':  fields.date(string=u"Date D'expiration de CIN"),
        'cnss':             fields.char(string=u"CNSS"),
        'piece_manquant':   fields.text(string=u"PIECE MANQUANTS"),
        'domiciliation':    fields.char(string=u"DOMICILIATION"),
        'appareil_tel':     fields.char(string=u"Appareil Tel"),
        'puce':             fields.char(string=u"Puce"),
        'abonnement':       fields.char(string=u"Abonnement"),
        'tablette':         fields.char(string=u"Tablette"),
        'pc_portable':      fields.char(string=u"PC Portable"),
        'voiture_marque':   fields.char(string=u"Marque de voiture"),
        'voiture_type':     fields.char(string=u"Type de voiture"),
        'voiture_matricule':fields.char(string=u"Matricule de voiture"),
        'carte_carburant_code':  fields.char(string=u"Code de Carte Carburant"),
        'carte_carburant_monatant':  fields.char(string=u"Montant Carte Carburant"),
        'carte_autoroute':  fields.char(string=u"Carte d'autoroute"),
        'cachet':           fields.char(string=u"Cachet"),
        "avantage":         fields.one2many("hr.employee.avantage","employee",u"avantage en nature"),
        "service":          fields.char("Service"),
        "address":          fields.char("Adresse"),
        "phone":            fields.char(u"Tél. personnel"),
        "rib":              fields.char(u"RIB"),
        "banque":           fields.char(u"banque"),
        "banque_agence":    fields.char(u"Agence bancaire"),
        "permis_conduire":  fields.char(u"Permis de conduire"),
    }
    
    @api.onchange('birthday')
    def check_age(self):
        if self.birthday:
            d1 = datetime.strptime(self.birthday, "%Y-%m-%d").date()
            d2 = date.today()
            self.age = relativedelta(d2, d1).years
    
    @api.onchange('date_embauche')
    def check_anc(self):
        if self.date_embauche:
            d1 = datetime.strptime(self.date_embauche, "%Y-%m-%d").date()
            d2 = date.today()
            self.anciennete = relativedelta(d2, d1).years


    def calc(self, cr,uid, context=None):
        ids  = self.search(cr,uid ,[])
        for o in self.browse(cr,uid,ids):
            #_logger.warning(u"WARNING: I don't think you want this to happen!  %s",o.name)
            if o.birthday:
                d1 = datetime.strptime(o.birthday, "%Y-%m-%d").date()
                d2 = date.today()
                o.age = relativedelta(d2, d1).years
            if o.date_embauche:
                d1 = datetime.strptime(o.date_embauche, "%Y-%m-%d").date()
                d2 = date.today()
                o.anciennete = relativedelta(d2, d1).years

    def name_get(self, cr, uid, ids, context=None):
        result = []
        for employee in self.browse(cr, uid, ids, context):
        
            name = (employee.matricule and ( employee.matricule + '-' ) or 'Sans matricule -')   + employee.name
            result.append((employee.id, name  ))
        
        return result


    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []

        ids = []
        if len(name) > 1:
            ids = self.search(cr, user, [('matricule', 'ilike', name)] + args, limit=limit, context=context)

        search_domain = [('name', operator, name)]
        if ids:
            search_domain.append(('id', 'not in', ids))
        ids.extend(self.search(cr, user, search_domain + args, limit=limit, context=context))

        locations = self.name_get(cr, user, ids, context)
        
        return sorted(locations, key=lambda (id ,name): ids.index(id))
        
        
class hr_employee_avantage(osv.osv):
    _name="hr.employee.avantage"
    _columns = {
        "name" : fields.char("Desc."),
        "valeur": fields.float(u"Valeur d'avantage"),
        "observations": fields.text("Observation"),
        "date_attribution": fields.date("Date d'attribution"),
        "employee":     fields.many2one("hr.employee",u"Employé"),
    
    }
    
    
class hr_holidays(osv.osv):
    _inherit = "hr.holidays"
    _columns = {
        "agence": fields.related('employee_id','agence', type='char', string='Agence'),
        "matricule": fields.related('employee_id','matricule', type='char', string='Matricule'),
        #"matricule" : fields.many2one('hr.employee',string='Matricule'),    
    }

    def onchange_date_from(self, cr, uid, ids, date_to, date_from):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            date_to_with_delta = datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(hours=8)
            result['value']['date_to'] = str(date_to_with_delta)

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            #diff_day = self.pool['resource.calendar'].get_working_hours( cr, uid, 2, start_dt = date_from, end_dt = date_to)


            result['value']['number_of_days_temp'] = int(diff_day) + ((diff_day - int(diff_day)) *3)
        else:
            result['value']['number_of_days_temp'] = 0

        return result

    def onchange_date_to(self, cr, uid, ids, date_to, date_from):
        """
        Update the number_of_days.
        """

        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['number_of_days_temp'] = int(diff_day) + ((diff_day - int(diff_day)) * 3)
        else:
            result['value']['number_of_days_temp'] = 0

        return result
    
    def onchange_days(self, cr, uid, ids, number_of_days_temp,date_from, context=None):
        if date_from:
            date_to_with_delta = datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=int(number_of_days_temp) , hours=(number_of_days_temp - int(number_of_days_temp)) * 8 )
            #raise Warning('test','%s' % date_to_with_delta)
            return {'value': {'date_to':str(date_to_with_delta)}}
            raise Warning('sss','sss')
            


class hr_employee_pret(osv.osv):
    _name="hr.employee.pret"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    _description = u"Avance / Crédit"
    
    
        
    _columns = {    
        'name':     fields.char('No. de bon', default='/', copy=False),
        'employee': fields.many2one('hr.employee',u'Employé',track_visibility="onchange"),
        'montant':  fields.float('Montant',track_visibility="onchange"),
        'motif':    fields.char('Motif',track_visibility="onchange"),
        'date' :    fields.date('Date',track_visibility="onchange"),
        'echeance': fields.date(u'Echéance',track_visibility="onchange"),
        'state' :   fields.selection(string="Etat",selection=(('new',u'Nouveau'),('confirmed',u'Confirmé'),('visa1',u'Validation responsable'),('visa2',u'Validation Chef Départ.'),('valide',u'Validation RH'),('paid',u'Payé'),('recouvered',u'Remboursé'),('cancel',u'Annulé'),('refuse',u'Refusé')), default='new',track_visibility="onchange",copy=False) ,  
        'type' :    fields.selection(string="Type",selection=(('c',u'Crédit'),('a',u'Avance')), required=True,) ,
        'mensualite': fields.integer(u'Mensualité',track_visibility="onchange"),
        'prime':      fields.integer(u'Nbr. décompte',track_visibility="onchange"),
        'reglement' : fields.one2many('hr.employee.pret.reglement','parent',u'Réglements',track_visibility="onchange"),
        'agence':     fields.many2one('hr.agence','Centre',track_visibility="onchange",oldname="hr_agence"),
        "matricule":  fields.related('employee','matricule', type='char', string='Matricule'),
        "ref_bank"  : fields.char(u"Virement/chèque"),
    }
    
    
    @api.one
    def _get_depense(self):
        res = self.env['hr.bon.caisse'].search([('operation','=','%s,%s' % (self._name, self.id))])
        self.depense_id = res
    depense_id = Fields.One2many('hr.bon.caisse',string=u'N° de dépense',compute=_get_depense)
        
    
    def forcer_validation(self,cr,uid,ids,context=None):
        for o in self.browse(cr,uid,ids):
            o.signal_workflow("visa1")
            o.signal_workflow("visa2")
            o.signal_workflow("valide")
            o.message_post(subject=u"VALIDATION FORCEE!",body="Document Validé par l'utilisateur ci-dessous'")
    
    def cancel_draft(self,cr,uid,ids,context=None):
        for o in self.browse(cr,uid,ids):
            o.delete_workflow()
            o.create_workflow()
            o.state = "new"
            o.message_post(subject=u"Réinitialisation forcée!",body="Document réinitialisé par l'utilisateur ci-dessous'")
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            if vals['type'] == 'c':
                seq_id = self.pool['hr.agence'].browse(cr,SUPERUSER_ID,vals['agence']).seq_credit._ids
            if vals['type'] == 'a':
                seq_id = self.pool['hr.agence'].browse(cr,SUPERUSER_ID,vals['agence']).seq_avance._ids                
            vals['name'] = self.pool.get('ir.sequence').next_by_id(cr, SUPERUSER_ID, seq_id, context=context) or '/'
        new_id = super(hr_employee_pret, self).create(cr, uid, vals, context=context)
        self.message_post(cr, uid, [new_id], body=u"Demande créée", context=context)
        return new_id
    
        
        
class hr_employee_pret_reglement(osv.osv):
    _name="hr.employee.pret.reglement"
    _columns = {
        'parent':   fields.many2one('hr.employee.pret','Parent'),
        'name':     fields.char('No. de bon'),
        'montant':  fields.float('Montant'),
        'date' :    fields.date('Date'),
     }
            
class hr_bon_caisse(osv.osv):
    _name="hr.bon.caisse"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Bon de caisse"
    
    @api.model
    def _get_operation(self):
        data = self._cr.execute("""select f.model , m.name from ir_model_fields f, ir_model m   where m.id=f.model_id and f.relation ='hr.bon.caisse' """)
        return self._cr.fetchall() or []
    
    _columns={
        'name' :        fields.char(u"Réf.", default="/",copy=False),
        'caisse':       fields.many2one('hr.caisse',string="Caisse",track_visibility="onchange"),
        'hr_agence':    fields.many2one('hr.agence','Centre',track_visibility="onchange"),
        'amount':       fields.float("Montant",track_visibility="onchange"),
        'destinataire': fields.many2one('hr.employee','Destinataire',track_visibility="onchange"),
        'state':        fields.selection([('new','Brouillon'),('confirmed',u'Confirmé'),('valide',u'Validation finance'),('paid',u'Payé'),('justified',u'Justifé'),('done','Términé'),('cancel',u'Annulé')],u'Etat',track_visibility="onchange",default="new",copy=False),
        'move_id':      fields.many2one("account.move",u'Pièce comptable',track_visibility="onchange"),
        'operation':    fields.reference(u'Opérations liées',_get_operation,track_visibility="onchange"),
        'date':         fields.date('Date',track_visibility="onchange",default=dt.now()),
        
        
   
    }
    
        

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            seq_id = 645
            agence = self.pool['hr.agence'].browse(cr,SUPERUSER_ID,vals['hr_agence'])
            caisse = self.pool['hr.caisse'].browse(cr,SUPERUSER_ID,vals['caisse'])
            name = self.pool.get('ir.sequence').next_by_id(cr, SUPERUSER_ID, seq_id, context=context) or '/'
            vals['name'] = name.replace('DP-', 'DP-%s-%s-' % (caisse.code,agence.code))
        new_id = super(hr_bon_caisse, self).create(cr, uid, vals, context=context)
        self.message_post(cr, uid, [new_id], body=u"Bon de caisse créé", context=context)
        return new_id

    @api.one
    def action_confirm(self):
        journal_id = self.env['account.journal'].search([('code','=','RHMG')])
        
        move_values                 = self.env['account.move'].default_get([])
        move_values['journal_id']   = journal_id.id
        move_values['ref']          = self.name
        move_values['name']         = self.name
        move_id                     = self.move_id.create(move_values)
        
        credit = {  'move_id':      move_id.id,
                    'name':         self.name,
                    'credit':       self.amount,
                    'account_id':   journal_id.default_credit_account_id.id,
                    'date':         self.date
                    }

        move_id.line_id.with_context(journal_id=journal_id.id, period_id = move_id.period_id.id ).create(credit)
        
        debit  = {  'move_id':      move_id.id,
                    'name':         self.name,
                    'debit':        self.amount,
                    'account_id':   journal_id.default_debit_account_id.id,
                    'date':         self.date
                    }
        move_id.line_id.with_context(journal_id=journal_id.id, period_id = move_id.period_id.id ).create(debit)
        
        self.move_id = move_id
        self.state= 'confirmed'

hr_bon_caisse()

class HrMission(models.Model):
    _inherit = 'hr.employee.mission'
    _description = 'Ordre de mission'

    matricule = Fields.Char(string='Matricule', related='employee_id.matricule')

    @api.one
    def _get_depense(self):
        res = self.env['hr.bon.caisse'].search([('operation','=','%s,%s' % (self._name, self.id))])
        self.depense_id = res
    depense_id = Fields.One2many('hr.bon.caisse',string=u'N° de dépense',compute=_get_depense)

class hr_caisse(osv.osv):
    _name='hr.caisse'
    _columns = {
    
        'name': fields.char("Nom"),
        'code': fields.char("Code",oldname='Code'),
        'caissier':fields.many2one("hr.employee","Caissier",oldname='Caissier')
    
    }


class hr_expense_expense(osv.osv):
    _inherit = "hr.expense.expense"
    _columns = {        
        "matricule": fields.related('employee_id','matricule', type='char', string='Matricule'),
    }







