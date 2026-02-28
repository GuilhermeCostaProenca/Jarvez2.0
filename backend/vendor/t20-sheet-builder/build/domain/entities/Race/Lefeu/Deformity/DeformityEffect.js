"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DeformityEffect = void 0;
const PassiveEffect_1 = require("../../../Ability/PassiveEffect");
const SheetBuilderError_1 = require("../../../../errors/SheetBuilderError");
const RaceAbilityName_1 = require("../../RaceAbilityName");
const Modifier_1 = require("../../../Modifier");
const AddFixedModifierToSkill_1 = require("../../../Action/AddFixedModifierToSkill");
class DeformityEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Todo lefou possui defeitos físicos que, embora desagradáveis, '
            + 'conferem certas vantagens. Você recebe +2 em '
            + 'duas perícias a sua escolha. Cada um desses bônus '
            + 'conta como um poder da '
            + 'Tormenta (mas não causam perda de Carisma). '
            + 'Você pode trocar um desses bônus por um poder da Tormenta a sua '
            + 'escolha (isso também '
            + 'não causa perda de '
            + 'Carisma).';
    }
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.versatile);
        this.choices = [];
    }
    addChoice(newChoice) {
        if (this.choices.length >= 2) {
            throw new SheetBuilderError_1.SheetBuilderError('EXCEEDED_CHOICES_QUANTITY');
        }
        const found = this.choices.find(choice => choice === newChoice);
        if (found) {
            throw new SheetBuilderError_1.SheetBuilderError('REPEATED_DEFORMITY_CHOICE');
        }
        this.choices.push(newChoice);
    }
    apply(transaction) {
        if (this.choices.length !== 2) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_DEFORMITIES_CHOICES');
        }
        this.choices.forEach(choice => {
            const modifier = new Modifier_1.FixedModifier(RaceAbilityName_1.RaceAbilityName.deformity, 2);
            transaction.run(new AddFixedModifierToSkill_1.AddFixedModifierToSkill({
                payload: {
                    modifier,
                    skill: choice,
                },
                transaction,
            }));
        });
    }
}
exports.DeformityEffect = DeformityEffect;
