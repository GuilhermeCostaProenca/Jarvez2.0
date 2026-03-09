import type { AbilityType } from '../Ability/Ability';
import { AbilityEffects } from '../Ability/AbilityEffects';
import type { RolePowerInterface } from '../Role/RolePower';
import { RolePowerName } from '../Role/RolePowerName';
import type { GeneralPowerInterface } from './GeneralPower/GeneralPower';
import { GeneralPowerName } from './GeneralPower/GeneralPowerName';
import type { PowerInterface, PowerType } from './Power';
import { GeneralPowerGroup } from './GeneralPower';
export declare class PowerFake implements PowerInterface {
    powerType: PowerType;
    name: GeneralPowerName;
    abilityType: AbilityType;
    addToSheet: import("vitest").Mock<any, any>;
    verifyRequirements: import("vitest").Mock<any, any>;
    effects: AbilityEffects<{}>;
}
export declare class GeneralPowerFake implements GeneralPowerInterface {
    group: GeneralPowerGroup;
    powerType: PowerType;
    name: GeneralPowerName;
    abilityType: AbilityType;
    addToSheet: import("vitest").Mock<any, any>;
    verifyRequirements: import("vitest").Mock<any, any>;
    effects: AbilityEffects<{}>;
    serialize: import("vitest").Mock<any, any>;
}
export declare class RolePowerFake implements RolePowerInterface {
    serialize: import("vitest").Mock<any, any>;
    powerType: PowerType;
    name: RolePowerName;
    abilityType: AbilityType;
    verifyRequirements: import("vitest").Mock<any, any>;
    addToSheet: import("vitest").Mock<any, any>;
    effects: AbilityEffects<{}>;
}
