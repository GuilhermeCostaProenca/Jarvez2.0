import { type AbilityEffectsInterface } from '../../../../../../Ability/AbilityEffects';
import { type AbilityLevel } from '../../../../../../Ability/AbilityLevel';
import { type Spell } from '../../../../../../Spell';
import { type SerializedArcanistLineage } from '../../../../SerializedArcanist';
import { ArcanistLineage } from '../ArcanistLineage';
import { ArcanistLineageType } from '../ArcanistLineageType';
import { ArcanistLineageFaerieCheatTrainingEffect } from './ArcanistLineageFaerieCheatTrainingEffect';
import { ArcanistLineageFaerieExtraSpellEffect } from './ArcanistLineageFaerieExtraSpellEffect';
export declare class ArcanistLineageFaerie extends ArcanistLineage {
    effects: Record<AbilityLevel, AbilityEffectsInterface> & {
        basic: {
            passive: {
                cheatTraining: ArcanistLineageFaerieCheatTrainingEffect;
                extraSpell: ArcanistLineageFaerieExtraSpellEffect;
            };
        };
    };
    readonly type = ArcanistLineageType.faerie;
    constructor(extraSpell: Spell);
    getExtraSpell(): Spell;
    serialize(): SerializedArcanistLineage;
}
