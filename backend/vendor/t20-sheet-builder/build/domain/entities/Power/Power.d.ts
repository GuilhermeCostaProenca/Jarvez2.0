import type { AbilityInterface } from '../Ability/Ability';
import { Ability } from '../Ability/Ability';
import { type SheetInterface } from '../Sheet/SheetInterface';
import type { PowerName } from './PowerName';
export type PowerType = 'general' | 'role' | 'origin' | 'granted';
export type PowerInterface = AbilityInterface & {
    name: PowerName;
    powerType: PowerType;
    verifyRequirements(sheet: SheetInterface): void;
};
export type RequirementInterface = {
    description: string;
    verify: (sheet: SheetInterface) => boolean;
};
export declare abstract class Power extends Ability implements PowerInterface {
    readonly name: PowerName;
    readonly powerType: PowerType;
    readonly requirements: RequirementInterface[];
    constructor(name: PowerName, powerType: PowerType);
    verifyRequirements(sheet: SheetInterface): void;
    protected addRequirement(requirement: RequirementInterface): void;
}
