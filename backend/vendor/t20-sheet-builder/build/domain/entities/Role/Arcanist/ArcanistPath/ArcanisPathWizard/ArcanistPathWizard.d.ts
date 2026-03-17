import { type AbilityEffectsInterface } from '../../../../Ability/AbilityEffects';
import type { Attribute } from '../../../../Sheet';
import type { SpellLearnFrequency } from '../../../SpellsAbility';
import { type SerializedArcanistPath } from '../../SerializedArcanist';
import { ArcanistPath, ArcanistPathName } from '../ArcanistPath';
import { type ArcanistPathWizardFocus } from './ArcanistPathWizardFocus';
import { ArcanistPathWizardFocusEffect } from './ArcanistPathWizardFocusEffect';
export declare class ArcanistPathWizard extends ArcanistPath {
    readonly focus: ArcanistPathWizardFocus;
    spellsAttribute: Attribute;
    spellLearnFrequency: SpellLearnFrequency;
    readonly pathName = ArcanistPathName.wizard;
    effects: AbilityEffectsInterface & {
        passive: {
            focus: ArcanistPathWizardFocusEffect;
        };
    };
    constructor(focus: ArcanistPathWizardFocus);
    getFocus(): ArcanistPathWizardFocus;
    serializePath(): SerializedArcanistPath;
}
