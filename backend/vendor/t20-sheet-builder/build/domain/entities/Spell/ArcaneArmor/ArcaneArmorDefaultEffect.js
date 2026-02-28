"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcaneArmorDefaultEffect = void 0;
const AffectableTarget_1 = require("../../Affectable/AffectableTarget");
const ManaCost_1 = require("../../ManaCost");
const SpellEffect_1 = require("../SpellEffect");
const SpellName_1 = require("../SpellName");
class ArcaneArmorDefaultEffect extends SpellEffect_1.SpellEffect {
    static get defenseBonus() {
        return 5;
    }
    static get duration() {
        return 'scene';
    }
    constructor() {
        super({
            source: SpellName_1.SpellName.arcaneArmor,
            duration: 'scene',
            execution: 'default',
        });
        this.description = 'Esta magia cria uma película protetora'
            + ' invisível, mas tangível, fornecendo'
            + ' +5 na Defesa. Esse bônus é cumulativo'
            + ' com outras magias, mas não com'
            + ' bônus fornecido por armaduras.';
        this.affectable = new AffectableTarget_1.AffectableTarget('self');
        this.baseCosts = [new ManaCost_1.ManaCost(1)];
        this.range = 'personal';
    }
}
exports.ArcaneArmorDefaultEffect = ArcaneArmorDefaultEffect;
