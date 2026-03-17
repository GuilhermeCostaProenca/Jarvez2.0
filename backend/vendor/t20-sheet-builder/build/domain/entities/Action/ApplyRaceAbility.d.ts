import { Action, type ActionSubClassParams } from './Action';
export declare class ApplyRaceAbility extends Action<'applyRaceAbility'> {
    constructor(params: ActionSubClassParams<'applyRaceAbility'>);
    execute(): void;
    getDescription(): string;
}
