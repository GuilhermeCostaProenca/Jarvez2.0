import { AbilityEffects } from '../AbilityEffects';
import { RolePlayEffect } from '../RolePlayEffect';
import { RaceAbility } from '../../Race/RaceAbility';
import { WildEmpathyRepeatedEffect } from './WildEmpathyRepeatedEffect';
export declare class WildEmpathy extends RaceAbility {
    static readonly effectDescription: string;
    effects: AbilityEffects<{
        roleplay: {
            default: RolePlayEffect;
        };
        passive: {
            repeated: WildEmpathyRepeatedEffect;
        };
    }>;
    constructor();
}
