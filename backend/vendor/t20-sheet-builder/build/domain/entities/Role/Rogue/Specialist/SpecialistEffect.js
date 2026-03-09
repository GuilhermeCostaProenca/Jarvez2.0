"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SpecialistEffect = void 0;
const Ability_1 = require("../../../Ability");
const ManaCost_1 = require("../../../ManaCost");
const Modifier_1 = require("../../../Modifier");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class SpecialistEffect extends Ability_1.TriggeredEffect {
    constructor(skills) {
        super({
            duration: 'immediate',
            execution: 'reaction',
            name: Ability_1.TriggeredEffectName.specialist,
            source: RoleAbilityName_1.RoleAbilityName.specialist,
            triggerEvents: Ability_1.TriggerEvent.skillTestExceptAttack,
        });
        this.baseCosts = [new ManaCost_1.ManaCost(1)];
        this.description = 'Escolha um número de perícias'
            + ' treinadas igual a sua Inteligência, exceto bônus'
            + ' temporários (mínimo 1). Ao fazer um teste de uma'
            + ' dessas perícias, você pode gastar 1 PM para dobrar'
            + ' seu bônus de treinamento. Você não pode usar esta'
            + ' habilidade em testes de ataque.';
        this.skills = new Set();
        this.skills = skills;
    }
    getSkills() {
        return [
            ...this.skills,
        ];
    }
    enable({ modifiersIndexes, modifiers }, activation) {
        var _a;
        const skillName = activation.skill.getName();
        if (!this.skills.has(skillName)) {
            throw new Error('INVALID_SPECIALIST_SKILL');
        }
        const trainingPoints = activation.skill.getTrainingPoints();
        const modifier = new Modifier_1.FixedModifier(RoleAbilityName_1.RoleAbilityName.specialist, trainingPoints);
        modifiersIndexes.skillExceptAttack = (_a = modifiers.skillExceptAttack) === null || _a === void 0 ? void 0 : _a.fixed.add(modifier);
        return {
            manaCost: this.baseCosts[0],
        };
    }
    disable({ modifiersIndexes, modifiers }) {
        var _a;
        if (modifiersIndexes.skillExceptAttack) {
            (_a = modifiers.skillExceptAttack) === null || _a === void 0 ? void 0 : _a.fixed.remove(modifiersIndexes.skillExceptAttack);
        }
    }
}
exports.SpecialistEffect = SpecialistEffect;
