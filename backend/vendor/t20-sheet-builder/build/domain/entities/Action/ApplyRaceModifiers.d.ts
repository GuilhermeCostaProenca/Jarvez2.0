import { Action, type ActionSubClassParams } from './Action';
export declare class ApplyRaceModifiers extends Action<'applyRaceModifiers'> {
    constructor(params: ActionSubClassParams<'applyRaceModifiers'>);
    execute(): void;
    getDescription(): string;
}
