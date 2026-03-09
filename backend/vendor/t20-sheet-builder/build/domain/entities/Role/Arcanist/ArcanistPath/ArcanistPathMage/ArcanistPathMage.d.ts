import { type AbilityEffectsInterface } from '../../../../Ability/AbilityEffects';
import type { Attribute } from '../../../../Sheet';
import type { Spell } from '../../../../Spell/Spell';
import type { SpellLearnFrequency } from '../../../SpellsAbility';
import { type SerializedArcanistPath } from '../../SerializedArcanist';
import { ArcanistPath, ArcanistPathName } from '../ArcanistPath';
import { ArcanistPathMageExtraSpellEffect } from './ArcanistPathMageExtraSpellEffect';
export declare class ArcanistPathMage extends ArcanistPath {
    effects: AbilityEffectsInterface & {
        passive: {
            extraSpell: ArcanistPathMageExtraSpellEffect;
        };
    };
    spellsAttribute: Attribute;
    spellLearnFrequency: SpellLearnFrequency;
    readonly pathName = ArcanistPathName.mage;
    constructor(additionalSpell: Spell);
    getExtraSpell(): Spell;
    serializePath(): SerializedArcanistPath;
}
