import { AbilityEffects } from '../../../Ability/AbilityEffects';
import { RaceAbility } from '../../RaceAbility';
import { HardAsRockInitialEffect } from './HardAsRockInitialEffect';
import { HardAsRockPerLevelEffect } from './HardAsRockPerLevelEffect';
export declare class HardAsRock extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            initial: HardAsRockInitialEffect;
            perLevel: HardAsRockPerLevelEffect;
        };
    }>;
    constructor();
}
