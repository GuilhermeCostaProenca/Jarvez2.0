"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SpellsAbilityEffect = void 0;
const PassiveEffect_1 = require("../Ability/PassiveEffect");
const LearnSpell_1 = require("../Action/LearnSpell");
const LearnCircle_1 = require("../Action/LearnCircle");
const SheetBuilderError_1 = require("../../errors/SheetBuilderError");
const SpellCircle_1 = require("../Spell/SpellCircle");
const AddFixedModifierToManaPoints_1 = require("../Action/AddFixedModifierToManaPoints");
const Modifier_1 = require("../Modifier");
class SpellsAbilityEffect extends PassiveEffect_1.PassiveEffect {
    constructor(spells, initialSpells, source, schools) {
        super(source);
        this.spells = spells;
        this.initialSpells = initialSpells;
        this.schools = schools;
        this.validateSpells();
    }
    apply(transaction) {
        this.learnCircle(transaction);
        this.learnSpells(transaction);
        this.addManaModifier(transaction);
    }
    addManaModifier(transaction) {
        transaction.run(new AddFixedModifierToManaPoints_1.AddFixedModifierToManaPoints({
            payload: {
                modifier: new Modifier_1.FixedModifier(this.source, 0, new Set([this.spellsAttribute])),
            },
            transaction,
        }));
    }
    learnCircle(transaction) {
        transaction.run(new LearnCircle_1.LearnCircle({
            payload: {
                circle: SpellCircle_1.SpellCircle.first,
                source: this.source,
                type: this.spellType,
                schools: this.schools,
            },
            transaction,
        }));
    }
    learnSpells(transaction) {
        this.spells.forEach(spell => {
            transaction.run(new LearnSpell_1.LearnSpell({
                payload: {
                    source: this.source,
                    spell,
                },
                transaction,
            }));
        });
    }
    validateSpells() {
        if (this.spells.length !== this.initialSpells) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_SPELLS_QUANTITY');
        }
    }
}
exports.SpellsAbilityEffect = SpellsAbilityEffect;
