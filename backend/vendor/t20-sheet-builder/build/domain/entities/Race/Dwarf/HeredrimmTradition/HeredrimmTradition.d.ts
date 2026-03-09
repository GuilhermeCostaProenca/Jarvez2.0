import { AbilityEffects } from '../../../Ability';
import { RaceAbility } from '../../RaceAbility';
import { HeredrimmTraditionEffect } from './HeredrimmTraditionEffect';
export declare class HeredrimmTradition extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: HeredrimmTraditionEffect;
        };
    }>;
    constructor();
}
