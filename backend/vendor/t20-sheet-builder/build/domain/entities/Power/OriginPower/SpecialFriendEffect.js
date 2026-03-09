"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SpecialFriendEffect = void 0;
const PassiveEffect_1 = require("../../Ability/PassiveEffect");
const AddFixedModifierToSkill_1 = require("../../Action/AddFixedModifierToSkill");
const SheetBuilderError_1 = require("../../../errors/SheetBuilderError");
const FixedModifier_1 = require("../../Modifier/FixedModifier/FixedModifier");
const SkillName_1 = require("../../Skill/SkillName");
const OriginPowerName_1 = require("./OriginPowerName");
class SpecialFriendEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return SpecialFriendEffect.description;
    }
    constructor(source, skill) {
        super(source);
        this.skill = skill;
        this.validateSkill();
    }
    apply(transaction) {
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
            payload: {
                modifier: new FixedModifier_1.FixedModifier(OriginPowerName_1.OriginPowerName.specialFriend, 5),
                skill: SkillName_1.SkillName.animalHandling,
            },
            transaction,
        }));
        transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
            payload: {
                modifier: new FixedModifier_1.FixedModifier(OriginPowerName_1.OriginPowerName.specialFriend, 2),
                skill: this.skill,
            },
            transaction,
        }));
    }
    validateSkill() {
        if (this.skill === SkillName_1.SkillName.fight || this.skill === SkillName_1.SkillName.aim) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_SKILL');
        }
    }
}
exports.SpecialFriendEffect = SpecialFriendEffect;
SpecialFriendEffect.description = 'Você recebe +5 em testes de Adestramento com animais.'
    + ' Além disso, possui um animal de estimação'
    + ' que o auxilia e o acompanha em suas aventuras. Em'
    + ' termos de jogo, é um parceiro que fornece +2 em'
    + ' uma perícia a sua escolha (exceto Luta ou Pontaria'
    + ' e aprovada pelo mestre) e não conta em seu limite'
    + ' de parceiros.';
