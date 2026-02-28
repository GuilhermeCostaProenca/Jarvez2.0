import { Action, type ActionSubClassParams } from './Action';
export declare class TrainSkill extends Action<'trainSkill'> {
    constructor(params: ActionSubClassParams<'trainSkill'>);
    execute(): void;
    getDescription(): string;
}
